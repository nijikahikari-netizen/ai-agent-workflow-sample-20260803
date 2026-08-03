package com.example.assetworkflow.employee;

import java.util.Objects;

public record Employee(Long id, EmployeeStatus status) {

  public Employee {
    Objects.requireNonNull(id, "id");
    Objects.requireNonNull(status, "status");
  }
}
