# from django.db import connection
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import AllowAny
# from rest_framework import status


# class RestaurantOrderListView(APIView):
#     permission_classes = [AllowAny]

#     def get(self, request):
#         resID = request.query_params.get("resID")

#         if not resID:
#             return Response(
#                 {"error": "resID is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         # 1️⃣ Restaurant-д хамаарах захиалгууд
#         with connection.cursor() as c:
#             c.execute("""
#                 SELECT DISTINCT
#                     o."orderID",
#                     o."userID",
#                     o."date",
#                     o."location",
#                     o."status"
#                 FROM tbl_order o
#                 JOIN tbl_orderfood ofd ON ofd."orderID" = o."orderID"
#                 JOIN tbl_food f ON f."foodID" = ofd."foodID"
#                 WHERE f."resID" = %s
#                 ORDER BY o."date" DESC
#             """, [resID])

#             orders = c.fetchall()

#         # ❗ Захиалга байхгүй үед
#         if not orders:
#             return Response(
#                 {
#                     "message": "Энэ рестораны захиалга одоогоор байхгүй байна",
#                     "data": []
#                 },
#                 status=status.HTTP_200_OK
#             )

#         result = []

#         # 2️⃣ Order бүрийн хоолнууд
#         for o in orders:
#             orderID, userID, date, location, status_val = o

#             with connection.cursor() as c:
#                 c.execute("""
#                     SELECT
#                         ofd."foodID",
#                         f."foodName",
#                         ofd."stock",
#                         ofd."price"
#                     FROM tbl_orderfood ofd
#                     JOIN tbl_food f ON f."foodID" = ofd."foodID"
#                     WHERE ofd."orderID" = %s
#                 """, [orderID])

#                 foods = c.fetchall()

#             food_list = [
#                 {
#                     "foodID": f[0],
#                     "foodName": f[1],
#                     "quantity": f[2],
#                     "price": f[3]
#                 }
#                 for f in foods
#             ]

#             result.append({
#                 "orderID": orderID,
#                 "userID": userID,
#                 "date": str(date),
#                 "location": location,
#                 "status": status_val,
#                 "foods": food_list
#             })

#         return Response(
#             {
#                 "message": "Захиалгын жагсаалт амжилттай татагдлаа",
#                 "data": result
#             },
#             status=status.HTTP_200_OK
#         )