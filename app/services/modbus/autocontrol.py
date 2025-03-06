import datetime
import os
from typing import Dict, Optional
import pandas as pd
from app.models.schemas import GlobalAutoControlConfig, GlobalAutoControlStatus, ServiceResult
from app.services.modbus.machine import MachineService
from app.core.logging_config import setup_logger
from app.api.dependencies import get_modbus_client_by_machine_name


logger = setup_logger(__name__)

# 로그 저장 경로
LOGS_DIR = "logs/autocontrol"
os.makedirs(LOGS_DIR, exist_ok=True)

class AutoControlService:
    # 싱글톤 패턴 구현을 위한 클래스 변수
    _instance = None
    _initialized = False
    
    # 전역 자동 제어 상태 (설정만 저장하고 비동기 태스크는 사용하지 않음)
    _global_auto_control_status: Optional[GlobalAutoControlStatus] = None
    
    def __new__(cls, machine_service: Optional[MachineService] = None):
        if cls._instance is None:
            cls._instance = super(AutoControlService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, machine_service: Optional[MachineService] = None):
        # 이미 초기화된 경우 스킵
        if AutoControlService._initialized and machine_service is None:
            return
            
        if machine_service:
            self.machine_service = machine_service
            AutoControlService._initialized = True
    
    def configure_auto_control(self, config: GlobalAutoControlConfig) -> ServiceResult:
        """전역 자동 제어 설정을 구성합니다."""        
        # 전역 설정 저장 (비동기 태스크 없이 설정만 저장)
        AutoControlService._global_auto_control_status = GlobalAutoControlStatus(
            enabled=config.enabled,
            machines=config.machines,
            last_executed=None
        )
        
        logger.info(f"자동 제어 설정 구성: {len(config.machines)}개 기계, 활성화 상태: {config.enabled}")
            
        return ServiceResult(
            success=True,
            message=f"자동 제어 설정이 구성되었습니다 (활성화: {config.enabled})",
            data=AutoControlService._global_auto_control_status
        )
    
    def toggle_auto_control(self, enabled: bool) -> ServiceResult:
        """자동 제어 모드를 켜거나 끕니다."""
        if AutoControlService._global_auto_control_status is None:
            return ServiceResult(
                success=False,
                message="자동 제어 설정이 구성되지 않았습니다"
            )
        
        AutoControlService._global_auto_control_status.enabled = enabled
        
        logger.info(f"자동 제어 상태 변경: 활성화={enabled}")
        
        return ServiceResult(
            success=True, 
            message=f"자동 제어 모드가 {'활성화' if enabled else '비활성화'}되었습니다",
            data=AutoControlService._global_auto_control_status
        )
    
    def get_auto_control_status(self) -> ServiceResult:
        """자동 제어 상태를 조회합니다."""
        if AutoControlService._global_auto_control_status is None:
            return ServiceResult(
                success=False,
                message="자동 제어 설정이 구성되지 않았습니다"
            )
        
        return ServiceResult(
            success=True,
            message="자동 제어 상태 조회 성공",
            data=AutoControlService._global_auto_control_status
        )
    
    async def execute_control(self, config: Optional[GlobalAutoControlConfig] = None) -> ServiceResult:
        """POST 요청시 호출되어 제어를 실행합니다.
        
        Args:
            config: 제어에 사용할 설정값. None이면 저장된 설정값 사용
        """
        # 설정값이 전달되면 그 설정값으로 제어, 아니면 기존 설정값 사용
        if config:
            # 설정값이 제공된 경우, 이를 저장하고 활성화 상태 확인
            control_config = config
            
            # 설정이 비활성화된 경우 제어하지 않음
            if not control_config.enabled:
                return ServiceResult(
                    success=False,
                    message="제공된 제어 설정이 비활성화 상태입니다"
                )
        else:
            # 설정값이 제공되지 않은 경우, 기존 저장된 설정값 사용
            if AutoControlService._global_auto_control_status is None:
                return ServiceResult(
                    success=False,
                    message="자동 제어 설정이 구성되지 않았습니다"
                )
                
            if not AutoControlService._global_auto_control_status.enabled:
                return ServiceResult(
                    success=False,
                    message="자동 제어가 비활성화 상태입니다"
                )
            
            control_config = GlobalAutoControlConfig(
                enabled=AutoControlService._global_auto_control_status.enabled,
                machines=AutoControlService._global_auto_control_status.machines
            )
        
        now = datetime.datetime.now()
        execution_log = {
            "timestamp": now.isoformat(),
            "controls": []
        }
        
        # 각 기계별로 제어 수행
        for machine_config in control_config.machines:
            machine_name = machine_config.machine_name
            
            try:
                # 해당 기계의 ModbusClient 가져오기
                client = await get_modbus_client_by_machine_name(machine_name)
                if not client:
                    logger.error(f"기계를 찾을 수 없음: {machine_name}")
                    continue
                
                # MachineService에 클라이언트 설정
                self.machine_service.client_manager = client
                
                # 각 태그별로 제어 수행
                for tag_config in machine_config.tags:
                    try:
                        # 태그 값 읽기
                        current_value = await self.machine_service.read_machine_tag_value(
                            machine_name, tag_config.tag_name
                        )
                        
                        # 현재 값과 목표 값 비교
                        if str(current_value) == tag_config.target_value:
                            # 이미 값이 같은 경우, write 작업 생략
                            logger.info(f"설정값이 동일함: {machine_name}.{tag_config.tag_name} = {current_value}, 제어 생략")
                            control_entry = {
                                "machine_name": machine_name,
                                "tag_name": tag_config.tag_name,
                                "previous_value": str(current_value),
                                "target_value": tag_config.target_value,
                                "status": "unchanged"  # 값이 변경되지 않았음을 표시
                            }
                            execution_log["controls"].append(control_entry)
                        else:
                            # 값이 다른 경우, write 작업 수행
                            result = await self.machine_service.write_machine_tag_value(
                                machine_name, tag_config.tag_name, tag_config.target_value
                            )
                            
                            # 제어 결과 기록
                            control_entry = {
                                "machine_name": machine_name,
                                "tag_name": tag_config.tag_name,
                                "previous_value": str(current_value),
                                "target_value": tag_config.target_value,
                                "status": "success" if result and result.success else "failed"
                            }
                            execution_log["controls"].append(control_entry)
                        
                    except Exception as e:
                        logger.error(f"태그 제어 실패: {machine_name}.{tag_config.tag_name} - {str(e)}")
                        execution_log["controls"].append({
                            "machine_name": machine_name,
                            "tag_name": tag_config.tag_name,
                            "previous_value": "unknown",
                            "target_value": tag_config.target_value,
                            "status": "error",
                            "error": str(e)
                        })
            except Exception as e:
                logger.error(f"기계 제어 실패: {machine_name} - {str(e)}")
        
        # 실행 결과 로그 저장
        if execution_log["controls"]:
            control_count = len(execution_log["controls"])
            unchanged_count = sum(1 for control in execution_log["controls"] if control["status"] == "unchanged")
            changed_count = control_count - unchanged_count
            
            logger.info(f"자동 제어 실행: {control_count}개 태그 중 {changed_count}개 변경, {unchanged_count}개 유지")
            
            # 상태 업데이트 (전역 상태 저장)
            if AutoControlService._global_auto_control_status:
                AutoControlService._global_auto_control_status.last_executed = now.isoformat()
            
            # 로그 저장
            self._save_log_to_parquet(execution_log)
            
            return ServiceResult(
                success=True,
                message=f"자동 제어 실행 완료: {control_count}개 태그 중 {changed_count}개 변경, {unchanged_count}개 유지",
                data={
                    "control_count": control_count,
                    "changed_count": changed_count,
                    "unchanged_count": unchanged_count,
                    "timestamp": now.isoformat()
                }
            )
        else:
            return ServiceResult(
                success=False,
                message="제어할 태그가 없거나 모든 제어가 실패했습니다"
            )
    
    def _save_log_to_parquet(self, execution_log: Dict):
        """단일 실행 로그를 Parquet 파일로 저장"""
        try:
            timestamp = execution_log["timestamp"]
            controls = execution_log["controls"]
            
            if not controls:
                return
            
            # 로그 파일 경로 설정
            log_date = datetime.datetime.fromisoformat(timestamp).strftime("%Y%m%d")
            log_file = f"{LOGS_DIR}/auto_control_{log_date}.parquet"
            
            # 각 제어 작업을 개별 로그 항목으로 변환
            log_entries = []
            for control in controls:
                entry = {
                    "timestamp": timestamp,
                    "machine": control["machine_name"],
                    "tag": control["tag_name"],
                    "previous_value": control["previous_value"],
                    "current_value": control["target_value"],
                    "status": control["status"],
                    "error_message": control.get("error", "")
                }
                log_entries.append(entry)
            
            df = pd.DataFrame(log_entries)
            
            # 기존 파일이 있으면 추가, 없으면 새로 생성
            if os.path.exists(log_file):
                existing_df = pd.read_parquet(log_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            # Parquet으로 저장
            df.to_parquet(log_file, index=False)
            logger.info(f"자동 제어 로그 저장 완료: {log_file} ({len(log_entries)}개 항목)")
        except Exception as e:
            logger.error(f"로그 저장 실패: {str(e)}")