# views/delivery.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..auth import JWTAuthentication
from ..database import execute_query

class DeliveryStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Хэрэглэгчийн хүргэлтийг авах
        deliveries = execute_query(
            """
            SELECT d.payID, d.orderID, d.status, ds.statusName, ds.description,
                   d.startdate, d.enddate,
                   w.workerName, w.phone, w.vehicleType, w.vehicleReg,
                   a.address, a.name as address_name, a.detail_adress
            FROM Хүргэлт d
            LEFT JOIN Хүргэлт_төлөв ds ON d.status = ds.statusID
            LEFT JOIN Хүргэлтийн_ажилтан w ON d.price = w.workerID
            LEFT JOIN Хаяг a ON a.userID = %s
            WHERE a.userID = %s
            ORDER BY d.startdate DESC
            """,
            (user['id'], user['id']),
            fetch_all=True
        )
        
        if not deliveries:
            return Response({'message': 'Хүргэлт олдсонгүй'}, status=200)
        
        return Response({'deliveries': deliveries}, status=200)
