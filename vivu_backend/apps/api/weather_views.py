"""Weather proxy views for the API app."""
from __future__ import annotations

import os
from typing import Any

import requests
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class WeatherProxyView(APIView):
    """Proxy current weather data from OpenWeather using backend-held API key."""

    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")

        if lat is None or lon is None:
            return Response(
                {"error": "Thiếu tham số lat hoặc lon."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat_value = float(lat)
            lon_value = float(lon)
        except (TypeError, ValueError):
            return Response(
                {"error": "lat hoặc lon không hợp lệ."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return Response(
                {"error": "OPENWEATHER_API_KEY chưa được cấu hình ở backend."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            response = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat_value,
                    "lon": lon_value,
                    "appid": api_key,
                    "units": "metric",
                    "lang": "vi",
                },
                timeout=8,
            )
            payload: Any = response.json()
        except requests.Timeout:
            return Response(
                {"error": "Yêu cầu thời tiết bị timeout."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.RequestException as exc:
            return Response(
                {"error": f"Không thể kết nối OpenWeather: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except ValueError:
            return Response(
                {"error": "Phản hồi thời tiết không phải JSON hợp lệ."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        if not response.ok:
            return Response(
                {
                    "error": "OpenWeather trả lỗi.",
                    "status_code": response.status_code,
                    "details": payload,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(payload, status=status.HTTP_200_OK)
