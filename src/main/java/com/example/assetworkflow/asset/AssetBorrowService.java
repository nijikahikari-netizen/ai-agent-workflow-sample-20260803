package com.example.assetworkflow.asset;

import com.example.assetworkflow.employee.Employee;
import com.example.assetworkflow.employee.EmployeeRepository;
import org.springframework.stereotype.Service;

@Service
public class AssetBorrowService {

  private final EmployeeRepository employeeRepository;
  private final AssetRepository assetRepository;
  private final BorrowRepository borrowRepository;

  public AssetBorrowService(
      EmployeeRepository employeeRepository,
      AssetRepository assetRepository,
      BorrowRepository borrowRepository) {
    this.employeeRepository = employeeRepository;
    this.assetRepository = assetRepository;
    this.borrowRepository = borrowRepository;
  }

  public BorrowResponse createBorrowRequest(Long employeeId, AssetBorrowRequest request) {
    Employee employee = employeeRepository.getById(employeeId);
    Asset asset = assetRepository.getAvailableById(request.assetId());
    Borrow borrow = Borrow.create(employee, asset, request.returnDueDate());
    borrowRepository.save(borrow);
    return BorrowResponse.from(borrow);
  }
}
