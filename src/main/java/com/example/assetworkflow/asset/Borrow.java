package com.example.assetworkflow.asset;

import com.example.assetworkflow.employee.Employee;
import java.time.LocalDate;
import java.util.Objects;

public record Borrow(Employee employee, Asset asset, LocalDate returnDueDate) {

  public Borrow {
    Objects.requireNonNull(employee, "employee");
    Objects.requireNonNull(asset, "asset");
    Objects.requireNonNull(returnDueDate, "returnDueDate");
  }

  public static Borrow create(Employee employee, Asset asset, LocalDate returnDueDate) {
    return new Borrow(employee, asset, returnDueDate);
  }
}
