import argparse
import glob
import os
import platform
import shutil
import stat
import subprocess

try:
  from ctypes import windll
  windll.kernel32.SetConsoleMode(windll.kernel32.GetStdHandle(-11), 7)
except ImportError:
  pass

_BAZEL_BIN_PATH = 'bazel-bin'
_BUILD_PATH = 'build'
_INSTALL_PATH = os.path.join('Packages', 'com.github.homuler.mediapipe', 'Runtime')

class Console:
  def __init__(self, verbose):
    self.verbose = verbose

  def v(self, message):
    if self.verbose > 0:
      self.log(33, 'DEBUG', message)

  def info(self, message):
    self.log(32, 'INFO', message)

  def error(self, message):
    self.log(31, 'INFO', message)

  def log(self, color, level, message):
    print('\033[' + str(color) + 'm' + level + '\033[0m (build.py): ' + message)


class Command:
  def __init__(self, command_args):
    self.console = Console(command_args.args.verbose)

  def _run_command(self, command_list):
    self.console.v(f"Running `{' '.join(command_list)}`")
    return subprocess.run(command_list, check=True)

  def _copy(self, source, dest, mode=0o755):
    self.console.v(f"Copying '{source}' to '{dest}'...")
    dest_dir = os.path.dirname(dest)

    if not os.path.exists(dest_dir):
      self.console.v(f"Creating '{dest_dir}'...")
      os.makedirs(dest_dir, 0o755)

    shutil.copy(source, dest)
    self.console.v(f"Changing the mode of '{dest}'...")
    os.chmod(dest, mode)

  def _copytree(self, source, dest):
    self.console.v(f"Copying '{source}' to '{dest}' recursively...")

    if not os.path.exists(dest):
      self.console.v(f"Creating '{dest}'...")
      os.makedirs(dest, 0o755)

    shutil.copytree(source, dest, dirs_exist_ok=True)

  def _remove(self, path):
    self.console.v(f"Removing '{path}'...")
    os.remove(path)

  def _rmtree(self, path):
    self.console.v(f"Removing '{path}'...")
    shutil.rmtree(path)

  def _unzip(self, source, dest):
    self.console.v(f"Unarchiving '{source}' to '{dest}'...")
    shutil.unpack_archive(source, dest)


class BuildCommand(Command):
  def __init__(self, command_args):
    Command.__init__(self, command_args)

    self.system = platform.system()
    self.desktop = command_args.args.desktop
    self.android = command_args.args.android
    self.ios= command_args.args.ios
    self.resources = command_args.args.resources
    self.include_opencv_libs = command_args.args.include_opencv_libs

    self.compilation_mode = command_args.args.compilation_mode
    self.strip_all = command_args.args.strip_all
    self.sandbox_debug = command_args.args.sandbox_debug
    self.verbose_failures = command_args.args.verbose_failures

  def run(self):
    self.console.info('Building protobuf sources...')
    self._run_command(self._build_proto_srcs_commands())
    self._unzip(
      os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'mediapipe_proto_srcs.zip'),
      os.path.join(_BUILD_PATH, 'Scripts', 'Protobuf'))
    self.console.info('Built protobuf sources')

    self.console.info('Downloading protobuf dlls...')
    self._run_command(self._build_proto_dlls_commands())

    for f in glob.glob(os.path.join('.nuget', '**', 'lib', 'netstandard2.0', '*.dll'), recursive=True):
      basename = os.path.basename(f)
      self._copy(f, os.path.join(_BUILD_PATH, 'Plugins', 'Protobuf', basename))

    self.console.info('Downloaded protobuf dlls')

    if self.resources:
      self.console.info('Building resource files')
      self._run_command(self._build_resources_commands())
      self._unzip(
        os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'mediapipe_assets.zip'),
        os.path.join(_BUILD_PATH, 'Resources'))

      self.console.info('Built resource files')

    if self.desktop:
      self.console.info('Building native libraries for Desktop...')
      self._run_command(self._build_desktop_commands())
      self._unzip(
        os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'mediapipe_desktop.zip'),
        os.path.join(_BUILD_PATH, 'Plugins'))

      if self.include_opencv_libs:
        self._run_command(self._build_opencv_libs())
        self._unzip(
          os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'opencv_libs.zip'),
          os.path.join(_BUILD_PATH, 'Plugins', 'OpenCV'))

      self.console.info('Built native libraries for Desktop')

    if self.android:
      self.console.info('Building native libraries for Android...')
      self._run_command(self._build_android_commands())
      self._copy(
        os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'java', 'com', 'github', 'homuler', 'mediapipe', 'mediapipe_android.aar'),
        os.path.join(_BUILD_PATH, 'Plugins', 'Android', 'mediapipe_android.aar'))

      self.console.info('Built native libraries for Android')

    if self.ios:
      self.console.info('Building native libaries for iOS...')
      self._run_command(self._build_ios_commands())
      self._unzip(
        os.path.join(_BAZEL_BIN_PATH, 'mediapipe_api', 'objc', 'MediaPipeUnity.zip'),
        os.path.join(_BUILD_PATH, 'Plugins', 'iOS'))

      self.console.info('Built native libraries for iOS')

    self.console.info('Installing...')

    if self.android:
      # When build Android AAR in linux-docker on windows, will copy build/* to host directory failed.
      # The path need to one up level.
      self._run_command(['cp', '-r', f'../{_BUILD_PATH}/*', _INSTALL_PATH])
    else:
      # _copytree fails on Windows, so run `cp -r` instead.
      self._run_command(['cp', '-r', f'{_BUILD_PATH}/*', _INSTALL_PATH])

    self.console.info('Installed')

  def _is_windows(self):
    return self.system == 'Windows'

  def _build_common_commands(self):
    commands = ['bazel']

    if self._is_windows():
      # limit the path length for Windows
      # @see https://docs.bazel.build/versions/master/windows.html#avoid-long-path-issues
      commands += ['--output_user_root', 'C:/_bzl']

    commands += ['build', '-c', self.compilation_mode]

    if self._is_windows():
      python_bin_path = os.environ['PYTHON_BIN_PATH'].replace('\\', '//')
      commands += ['--action_env', f'PYTHON_BIN_PATH={python_bin_path}']

    if self.strip_all:
      commands.append('--linkopt=-s')

    if self.sandbox_debug:
      commands.append('--sandbox_debug')

    if self.verbose_failures:
      commands.append('--verbose_failures')

    return commands

  def _build_desktop_commands(self):
    if self.desktop is None:
      return []

    commands = self._build_common_commands()

    if self.desktop == 'gpu':
      commands += ['--copt', '-DMESA_EGL_NO_X11_HEADERS', '--copt', '-DEGL_NO_X11']
    else:
      commands += ['--define', 'MEDIAPIPE_DISABLE_GPU=1']

    commands.append('//mediapipe_api:mediapipe_desktop')
    return commands

  def _build_opencv_libs(self):
    if not self.include_opencv_libs:
      return []

    commands = self._build_common_commands()
    commands.append('//mediapipe_api:opencv_libs')
    return commands


  def _build_android_commands(self):
    if self.android is None:
      return []

    commands = self._build_common_commands()
    commands.append(f'--config=android_{self.android}')
    commands.append('//mediapipe_api/java/com/github/homuler/mediapipe:mediapipe_android')
    return commands

  def _build_ios_commands(self):
    if self.ios is None:
      return []

    commands = self._build_common_commands()
    commands += [f'--config=ios_{self.ios}', '--copt=-fembed-bitcode', '--apple_bitcode=embedded']
    commands.append('//mediapipe_api/objc:MediaPipeUnity')
    return commands

  def _build_resources_commands(self):
    if not self.resources:
      return []

    commands = self._build_common_commands()
    commands.append('//mediapipe_api:mediapipe_assets')
    return commands

  def _build_proto_srcs_commands(self):
    commands = self._build_common_commands()
    commands.append('//mediapipe_api:mediapipe_proto_srcs')
    return commands

  def _build_proto_dlls_commands(self):
    return ['nuget', 'install', '-o', '.nuget']


class CleanCommand(Command):
  def __init__(self, command_args):
    Command.__init__(self, command_args)

  def run(self):
    self._rmtree(_BUILD_PATH)
    self._run_command(['bazel', 'clean', '--expunge'])


class UninstallCommand(Command):
  def __init__(self, command_args):
    Command.__init__(self, command_args)

    self.desktop = command_args.args.desktop
    self.android = command_args.args.android
    self.ios = command_args.args.ios
    self.resources = command_args.args.resources
    self.protobuf = command_args.args.protobuf

  def run(self):
    if self.desktop:
      self.console.info('Uninstalling native libraries for Desktop...')
      for f in glob.glob(os.path.join(_INSTALL_PATH, 'Plugins', '*'), recursive=True):
        if f.endswith('.dll') or f.endswith('.dylib') or f.endswith('.so'):
          self._remove(f)

    if self.android:
      self.console.info('Uninstalling native libraries for Android...')

      aar_path = os.path.join(_INSTALL_PATH, 'Plugins', 'Android', 'mediapipe_android.aar')

      if os.path.exists(aar_path):
        self._remove(aar_path)

    if self.ios:
      self.console.info('Uninstalling native libraries for iOS...')

      ios_framework_path = os.path.join(_INSTALL_PATH, 'Plugins', 'iOS', 'MediaPipeUnity.framework')

      if os.path.exists(ios_framework_path):
        self._rmtree(ios_framework_path)

    if self.resources:
      self.console.info('Uninstalling resource files...')

      for f in glob.glob(os.path.join(_INSTALL_PATH, 'Resources', '*'), recursive=True):
        if not f.endswith('.meta'):
          self._remove(f)

    if self.protobuf:
      self.console.info('Uninstalling protobuf sources and dlls...')

      for f in glob.glob(os.path.join(_INSTALL_PATH, 'Plugins', 'Protobuf', '*.dll'), recursive=True):
        self._remove(f)

      for f in glob.glob(os.path.join(_INSTALL_PATH, 'Scripts', 'Protobuf', '*'), recursive=True):
        if not f.endswith('.meta'):
          self._remove(f)


class HelpCommand(Command):
  def __init__(self, args):
    self.args = args

  def run(self):
    self.args.argument_parser.print_help()


class Argument:
  argument_parser = None
  args = None

  def __init__(self):
    self.argument_parser = argparse.ArgumentParser()
    subparsers = self.argument_parser.add_subparsers(dest='command')

    build_command_parser = subparsers.add_parser('build', help='Build and install native libraries')
    build_command_parser.add_argument('--desktop', choices=['cpu', 'gpu'])
    build_command_parser.add_argument('--android', choices=['arm', 'arm64'])
    build_command_parser.add_argument('--ios', choices=['arm64'])
    build_command_parser.add_argument('--resources', action=argparse.BooleanOptionalAction, default=True)
    build_command_parser.add_argument('--compilation_mode', '-c', choices=['fastbuild', 'opt', 'debug'], default='opt')
    build_command_parser.add_argument('--include_opencv_libs', action='store_true', help='Include OpenCV\'s native libraries for Desktop')
    build_command_parser.add_argument('--strip_all', '-s', action='store_true', help='Omit all symbol information from the output file')
    build_command_parser.add_argument('--sandbox_debug', action='store_true')
    build_command_parser.add_argument('--verbose_failures', action='store_true')
    build_command_parser.add_argument('--verbose', '-v', action='count', default=0)

    clean_command_parser = subparsers.add_parser('clean', help='Clean temporary files')
    clean_command_parser.add_argument('--verbose', '-v', action='count', default=0)

    uninstall_command_parser = subparsers.add_parser('uninstall', help='Uninstall native libraries')
    uninstall_command_parser.add_argument('--desktop', action=argparse.BooleanOptionalAction, default=True)
    uninstall_command_parser.add_argument('--android', action=argparse.BooleanOptionalAction, default=True)
    uninstall_command_parser.add_argument('--ios', action=argparse.BooleanOptionalAction, default=True)
    uninstall_command_parser.add_argument('--resources', action=argparse.BooleanOptionalAction, default=True)
    uninstall_command_parser.add_argument('--protobuf', action=argparse.BooleanOptionalAction, default=True)
    uninstall_command_parser.add_argument('--verbose', '-v', action='count', default=0)

    self.args = self.argument_parser.parse_args()

  def command(self):
    if self.args.command == 'build':
      return BuildCommand(self)
    elif self.args.command == 'clean':
      return CleanCommand(self)
    elif self.args.command == 'uninstall':
      return UninstallCommand(self)
    else:
      return HelpCommand(self)


Argument().command().run()
