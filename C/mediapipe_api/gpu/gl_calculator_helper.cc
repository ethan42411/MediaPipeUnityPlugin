#include <utility>
#include "mediapipe_api/gpu/gl_calculator_helper.h"

MpReturnCode mp_GlCalculatorHelper__(mediapipe::GlCalculatorHelper** gl_calculator_helper_out) {
  TRY {
    *gl_calculator_helper_out = new mediapipe::GlCalculatorHelper();
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

void mp_GlCalculatorHelper__delete(mediapipe::GlCalculatorHelper* gl_calculator_helper) {
  delete gl_calculator_helper;
}

MpReturnCode mp_GlCalculatorHelper__InitializeForTest__Pgr(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                           mediapipe::GpuResources* gpu_resources) {
  TRY {
    gl_calculator_helper->InitializeForTest(gpu_resources);
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

MpReturnCode mp_GlCalculatorHelper__RunInGlContext__PF(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                       NativeGlStatusFunction* gl_func,
                                                       mediapipe::Status** status_out) {
  TRY {
    auto status = gl_calculator_helper->RunInGlContext([&gl_func]() -> ::mediapipe::Status {
      return mediapipe::Status { std::move(*(gl_func())) };
    });
    *status_out = new mediapipe::Status { std::move(status) };
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

MpReturnCode mp_GlCalculatorHelper__CreateSourceTexture__Rif(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                             mediapipe::ImageFrame* image_frame,
                                                             mediapipe::GlTexture** gl_texture_out) {
  TRY_ALL {
    *gl_texture_out = new mediapipe::GlTexture { gl_calculator_helper->CreateSourceTexture(std::move(*image_frame)) };
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_ALL
}

MpReturnCode mp_GlCalculatorHelper__CreateSourceTexture__Rgb(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                             mediapipe::GpuBuffer* gpu_buffer,
                                                             mediapipe::GlTexture** gl_texture_out) {
  TRY_ALL {
    *gl_texture_out = new mediapipe::GlTexture { gl_calculator_helper->CreateSourceTexture(std::move(*gpu_buffer)) };
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_ALL
}

MpReturnCode mp_GlCalculatorHelper__CreateDestinationTexture__i_i_ui(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                                              int output_width,
                                                                              int output_height,
                                                                              mediapipe::GpuBufferFormat format,
                                                                              mediapipe::GlTexture** gl_texture_out) {
  TRY {
    *gl_texture_out = new mediapipe::GlTexture {
      gl_calculator_helper->CreateDestinationTexture(
        output_width,
        output_height,
        format)
    };
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

GLuint mp_GlCalculatorHelper__framebuffer(mediapipe::GlCalculatorHelper* gl_calculator_helper) {
  return gl_calculator_helper->framebuffer();
}

MpReturnCode mp_GlCalculatorHelper__BindFrameBuffer__Rtexture(mediapipe::GlCalculatorHelper* gl_calculator_helper,
                                                             mediapipe::GlTexture* gl_texture) {
  TRY {
    gl_calculator_helper->BindFramebuffer(std::move(*gl_texture));
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

bool mp_GlCalculatorHelper__Initialized(mediapipe::GlCalculatorHelper* gl_calculator_helper) {
  return gl_calculator_helper->Initialized();
}

MpReturnCode mp_GlTexture__(mediapipe::GlTexture** gl_texture_out) {
  TRY {
    *gl_texture_out = new mediapipe::GlTexture();
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

MpReturnCode mp_GlTexture__ui_i_i(GLuint name, int width, int height, mediapipe::GlTexture** gl_texture_out) {
  TRY {
    *gl_texture_out = new mediapipe::GlTexture { name, width, height };
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

void mp_GlTexture__delete(mediapipe::GlTexture* gl_texture) {
  delete gl_texture;
}

int mp_GlTexture__width(mediapipe::GlTexture* gl_texture) {
  return gl_texture->width();
}

int mp_GlTexture__height(mediapipe::GlTexture* gl_texture) {
  return gl_texture->height();
}

GLenum mp_GlTexture__target(mediapipe::GlTexture* gl_texture) {
  return gl_texture->target();
}

GLuint mp_GlTexture__name(mediapipe::GlTexture* gl_texture) {
  return gl_texture->name();
}

MpReturnCode mp_GlTexture__Release(mediapipe::GlTexture* gl_texture) {
  TRY {
    gl_texture->Release();
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}

MpReturnCode mp_GlTexture__GetGpuBufferFrame(mediapipe::GlTexture* gl_texture, mediapipe::GpuBuffer** gpu_buffer_out) {
  TRY {
    *gpu_buffer_out = gl_texture->GetFrame<mediapipe::GpuBuffer>().release();
    RETURN_CODE(MpReturnCode::Success);
  } CATCH_EXCEPTION
}
