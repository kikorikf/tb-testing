import httpx
from app.core.config import settings


async def _get_service_token() -> str:
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            settings.keycloak_token_uri,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.keycloak_backend_client_id,
                "client_secret": settings.keycloak_backend_client_secret,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def get_shifts(employee_id: int, shift_date: str) -> list[dict]:
    token = await _get_service_token()
    async with httpx.AsyncClient(verify=settings.wfm_verify_ssl) as client:
        resp = await client.get(
            f"{settings.wfm_base_url}/shift",
            params={"employeeId": employee_id, "shiftDate": shift_date},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def post_shift(employee_id: int, start_time: str, end_time: str) -> dict:
    token = await _get_service_token()
    async with httpx.AsyncClient(verify=settings.wfm_verify_ssl) as client:
        resp = await client.post(
            f"{settings.wfm_base_url}/shift",
            json={"employeeId": employee_id, "startTime": start_time, "endTime": end_time},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()
