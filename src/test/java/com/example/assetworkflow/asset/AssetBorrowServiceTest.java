package com.example.assetworkflow.asset;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.BDDMockito.then;

import com.example.assetworkflow.employee.Employee;
import com.example.assetworkflow.employee.EmployeeRepository;
import com.example.assetworkflow.employee.EmployeeStatus;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class AssetBorrowServiceTest {

  private static final long EMPLOYEE_ID = 1L;
  private static final long ASSET_ID = 10L;

  @Mock private EmployeeRepository employeeRepository;
  @Mock private AssetRepository assetRepository;
  @Mock private BorrowRepository borrowRepository;
  @InjectMocks private AssetBorrowService service;

  @Test
  void activeEmployeeCanCreateBorrowRequest() {
    BorrowResponse result = executeSuccessfulBorrow(EmployeeStatus.ACTIVE);

    assertThat(result.employeeId()).isEqualTo(EMPLOYEE_ID);
    then(borrowRepository).should().save(any(Borrow.class));
  }

  @Test
  void leaveEmployeeKeepsBaselineBorrowBehavior() {
    BorrowResponse result = executeSuccessfulBorrow(EmployeeStatus.LEAVE);

    assertThat(result.assetId()).isEqualTo(ASSET_ID);
    then(borrowRepository).should().save(any(Borrow.class));
  }

  @Test
  void resignedEmployeeCanCreateBorrowRequestInBaseline() {
    BorrowResponse result = executeSuccessfulBorrow(EmployeeStatus.RESIGNED);

    assertThat(result).isNotNull();
    then(borrowRepository).should().save(any(Borrow.class));
  }

  @Test
  void businessExceptionExposesExistingErrorCodeContract() {
    BusinessException exception = new BusinessException(ErrorCode.INVALID_BORROW_REQUEST);

    assertThat(exception.getErrorCode()).isEqualTo(ErrorCode.INVALID_BORROW_REQUEST);
    assertThat(exception.getMessage()).isEqualTo("INVALID_BORROW_REQUEST");
  }

  private BorrowResponse executeSuccessfulBorrow(EmployeeStatus status) {
    Employee employee = new Employee(EMPLOYEE_ID, status);
    given(employeeRepository.getById(EMPLOYEE_ID)).willReturn(employee);
    given(assetRepository.getAvailableById(ASSET_ID)).willReturn(new Asset(ASSET_ID));

    return service.createBorrowRequest(
        EMPLOYEE_ID, new AssetBorrowRequest(ASSET_ID, LocalDate.now().plusDays(7)));
  }
}
