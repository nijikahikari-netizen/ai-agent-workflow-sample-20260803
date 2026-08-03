package com.example.assetworkflow.asset;

import java.util.Objects;

public class BusinessException extends RuntimeException {

  private final ErrorCode errorCode;

  public BusinessException(ErrorCode errorCode) {
    super(errorCode.name());
    this.errorCode = Objects.requireNonNull(errorCode, "errorCode");
  }

  public ErrorCode getErrorCode() {
    return errorCode;
  }
}
