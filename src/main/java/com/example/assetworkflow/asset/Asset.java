package com.example.assetworkflow.asset;

import java.util.Objects;

public record Asset(Long id) {

  public Asset {
    Objects.requireNonNull(id, "id");
  }
}
