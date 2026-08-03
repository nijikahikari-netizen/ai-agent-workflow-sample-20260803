package com.example.assetworkflow.asset;

import java.time.LocalDate;
import java.util.Objects;

public record AssetBorrowRequest(Long assetId, LocalDate returnDueDate) {

  public AssetBorrowRequest {
    Objects.requireNonNull(assetId, "assetId");
    Objects.requireNonNull(returnDueDate, "returnDueDate");
  }
}
