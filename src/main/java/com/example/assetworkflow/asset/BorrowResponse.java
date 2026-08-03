package com.example.assetworkflow.asset;

public record BorrowResponse(Long employeeId, Long assetId) {

  public static BorrowResponse from(Borrow borrow) {
    return new BorrowResponse(borrow.employee().id(), borrow.asset().id());
  }
}
