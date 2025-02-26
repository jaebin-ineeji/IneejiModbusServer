from typing import Dict, List, Optional
import json
import asyncio
from fastapi import WebSocket
from app.models.schemas import ApiResponse, ErrorResponse
from app.services.modbus.machine import MachineService
from app.services.modbus.client import ModbusClientManager
from app.core.logging_config import setup_logger

logger = setup_logger(__name__)


class WebSocketService:
    def __init__(self, machine_service: MachineService):
        self.machine_service = machine_service
        self._running = True  # 웹소켓 연결 상태 관리를 위한 플래그 추가

    async def handle_single_machine_monitoring(
        self, websocket: WebSocket, machine_name: str, client: ModbusClientManager
    ) -> None:
        """단일 기계의 태그 모니터링을 처리"""
        self.machine_service.client_manager = client

        try:
            initial_message = await websocket.receive_text()
            tag_names = json.loads(initial_message).get("tag_names", "").split(",")
            tag_list = [tag.strip() for tag in tag_names]

            while self._running:  # 플래그를 통한 루프 제어
                try:
                    data = await self._read_machine_tags(machine_name, tag_list)
                    await self._send_response(
                        websocket,
                        True,
                        f"{machine_name.upper()} 기계의 선택한 태그 값 조회 성공",
                        data,
                    )
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.error(f"태그 읽기 오류: {str(e)}")  # 로깅 추가
                    await self._send_error_response(
                        websocket, "태그 값 조회 실패", str(e)
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"웹소켓 에러 발생: {str(e)}")
        finally:
            self._running = False  # 연결 종료 시 플래그 리셋
            await self._cleanup()  # 리소스 정리를 위한 메서드 추가

    async def handle_multiple_machines_monitoring(
        self,
        websocket: WebSocket,
    ) -> None:
        """다중 기계의 태그 모니터링을 처리"""
        machines_config = {}

        try:
            while True:
                try:
                    machines_config = await self._update_machines_config(
                        websocket, machines_config
                    )
                    if not machines_config:
                        await asyncio.sleep(1)
                        continue

                    all_data = await self._read_multiple_machines_tags(machines_config)
                    await self._send_response(
                        websocket, True, "기계별 태그 값 조회 성공", all_data
                    )
                    await asyncio.sleep(1)

                except Exception as e:
                    await self._send_error_response(
                        websocket, "데이터 조회 실패", str(e)
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"웹소켓 에러 발생: {str(e)}")

    async def _read_machine_tags(self, machine_name: str, tag_list: List[str]) -> Dict:
        """단일 기계의 태그 값들을 읽음"""
        tasks = [
            self.machine_service.read_machine_tag_value(machine_name, tag.upper())
            for tag in tag_list
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data = {}
        for tag, result in zip(tag_list, results):
            if isinstance(result, Exception):
                data[tag.upper()] = f"오류 발생: {str(result)}"
            else:
                data[tag.upper()] = result
        return data

    async def _read_multiple_machines_tags(self, machines_config: Dict) -> Dict:
        """여러 기계의 태그 값들을 읽음"""
        all_data = {}
        for machine_name, tag_names in machines_config.items():
            try:
                client = await self._get_modbus_client(machine_name)
                self.machine_service.client_manager = client

                tag_list = [tag.strip().upper() for tag in tag_names]
                machine_data = await self._read_machine_tags(machine_name, tag_list)
                all_data[machine_name] = machine_data

            except Exception as machine_error:
                all_data[machine_name] = f"기계 데이터 조회 실패: {str(machine_error)}"

        return all_data

    async def _update_machines_config(
        self, websocket: WebSocket, current_config: Dict
    ) -> Dict:
        """기계 설정 업데이트"""
        try:
            message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
            message_data = json.loads(message)
            if isinstance(message_data, dict):
                logger.info(f"태그 모니터링 설정이 업데이트되었습니다: {message_data}")
                return message_data
        except asyncio.TimeoutError:
            return current_config
        except json.JSONDecodeError:
            await self._send_error_response(
                websocket,
                "잘못된 메시지 형식입니다",
                "JSON 형식이 올바르지 않습니다",
                "INVALID_MESSAGE_FORMAT",
            )
            return current_config
        return current_config

    @staticmethod
    async def _send_response(
        websocket: WebSocket, success: bool, message: str, data: Optional[Dict] = None
    ) -> None:
        """응답 전송"""
        await websocket.send_json(
            ApiResponse(success=success, message=message, data=data).model_dump(
                exclude_none=True
            )
        )

    @staticmethod
    async def _send_error_response(
        websocket: WebSocket,
        message: str,
        error_message: str,
        error_code: str = "TAG_READ_ERROR",
    ) -> None:
        """에러 응답 전송"""
        await websocket.send_json(
            ApiResponse(
                success=False,
                message=message,
                error=ErrorResponse(code=error_code, message=error_message),
            ).model_dump()
        )

    @staticmethod
    async def _get_modbus_client(machine_name: str) -> ModbusClientManager:
        """ModbusClient 인스턴스 가져오기"""
        from app.api.dependencies import get_modbus_client_by_machine_name

        return await get_modbus_client_by_machine_name(machine_name)

    async def _cleanup(self) -> None:
        """리소스 정리를 위한 메서드"""
        try:
            if self.machine_service.client_manager:
                self.machine_service.client_manager.close_all()
        except Exception as e:
            logger.error(f"정리 중 오류 발생: {str(e)}")
