from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

class ConfirmOrderView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response(
                {"error": "order_id шаардлагатай"},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT status FROM tbl_order WHERE "orderID" = %s',
                [order_id]
            )
            row = cursor.fetchone()

            if not row:
                return Response(
                    {"error": "Захиалга олдсонгүй"},
                    status=status.HTTP_404_NOT_FOUND
                )

            if row[0] == "CONFIRMED":
                return Response(
                    {"message": "Захиалга аль хэдийн баталгаажсан"},
                    status=status.HTTP_200_OK
                )

            cursor.execute(
                '''
                UPDATE tbl_order
                SET status = %s
                WHERE "orderID" = %s
                ''',
                ["CONFIRMED", order_id]
            )

        return Response(
            {
                "message": "OK",
                "order_id": order_id,
                "status": "CONFIRMED"
            },
            status=status.HTTP_200_OK
        )

