import asyncio
import datetime
import decimal
from typing import List, Optional
import localtime

import httpx
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

import logging

logger = logging.getLogger("octopus")
logger.setLevel(logging.DEBUG)


class HHReading(BaseModel):
    start_at: datetime.datetime
    end_at: datetime.datetime
    version: str
    value: decimal.Decimal


class Octopus:
    AUTH_BODY = """
    mutation obtainKrakenToken($input: ObtainJSONWebTokenInput!) {
      obtainKrakenToken(input: $input) {
        refreshToken
        refreshExpiresIn
        payload
        token
      }
    }
    """

    GET_ACCOUNT_BODY = """
    query accountViewer {
      viewer {
        accounts {
          number
        }
      }
    }
    """

    GET_HH_BODY = """
    query halfHourlyReadings($accountNumber: String!, $fromDatetime: DateTime, $toDatetime: DateTime) {
      account(accountNumber: $accountNumber) {
        properties {
          electricitySupplyPoints {
            halfHourlyReadings(fromDatetime: $fromDatetime, toDatetime: $toDatetime) {
              startAt
              endAt
              version
              value
            }
          }
        }
      }
    }
    """

    def __init__(self, email: str, password: str, api_url: str):
        self.email = email
        self.password = password
        self.api_url = api_url

    async def check_auth(self) -> bool:
        try:
            await self.get_token()
        except ValueError:
            return False
        else:
            return True

    async def get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.api_url,
                json={
                    "query": self.AUTH_BODY,
                    "variables": {
                        "input": {
                            "email": self.email,
                            "password": self.password,
                        }
                    },
                },
            )
            response_dict = response.json()
            await self._validate_response(response_dict)

            return response_dict["data"]["obtainKrakenToken"]["token"]

    async def get_account_number(self) -> str:
        token = await self.get_token()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.api_url,
                json={
                    "query": self.GET_ACCOUNT_BODY,
                },
                headers={"authorization": f"JWT {token}"},
            )
            response_dict = response.json()
            await self._validate_response(response_dict)

            return response_dict["data"]["viewer"]["accounts"][0]["number"]

    async def get_hh_readings(
        self,
        start_at: datetime.datetime,
        end_at: Optional[datetime.datetime] = None,
    ) -> List[HHReading]:
        token = await self.get_token()
        number = await self.get_account_number()

        variables = {
            "accountNumber": number,
            "fromDatetime": start_at.isoformat(),
        }
        if end_at:
            variables["toDatetime"] = end_at.isoformat()

        print(f"{variables=}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.api_url,
                json={
                    "query": self.GET_HH_BODY,
                    "variables": variables,
                },
                headers={"authorization": f"JWT {token}"},
            )
            response_dict = response.json()
            await self._validate_response(response_dict)

            readings_raw = response_dict["data"]["account"]["properties"][0][
                "electricitySupplyPoints"
            ][0]["halfHourlyReadings"]
            readings: List[HHReading] = []
            for reading_raw in readings_raw:
                readings.append(
                    HHReading(
                        start_at=datetime.datetime.fromisoformat(
                            reading_raw["startAt"]
                        ),
                        end_at=datetime.datetime.fromisoformat(reading_raw["endAt"]),
                        version=reading_raw["version"],
                        value=decimal.Decimal(reading_raw["value"]),
                    )
                )

            return readings

    @staticmethod
    async def _validate_response(response_dict: dict) -> None:
        if (errors := response_dict.get("errors")) and len(errors):
            raise ValueError(errors)


class OctopusSettings(BaseSettings):
    email: str = None
    password: str = None
    api_url: str = Field(default="https://api.oejp-kraken.energy/v1/graphql/")

    class Config:
        extra = "ignore"
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "OCTOPUS_"

    def get_octopus(self) -> Octopus:
        return Octopus(self.email, self.password, self.api_url)


async def main():
    settings = OctopusSettings()
    octopus = settings.get_octopus()

    # get last 3 days
    end_date = localtime.now()
    start_date = localtime.days_in_the_past(3, end_date)

    readings = await octopus.get_hh_readings(
        start_at=localtime.midnight(start_date),
        end_at=localtime.midnight(end_date),
    )

    print(f"{readings=}")


if __name__ == "__main__":
    asyncio.run(main())
