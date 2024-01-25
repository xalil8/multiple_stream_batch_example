cameras_data = {
    "1": [
        {
            "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.5:554/Streaming/Channels/1/",
            "CameraId": "1",
            "Poly": [
                [534, 293],
                [489, 267],
                [497, 220],
                [534, 209],
                [543, 185],
                [483, 184],
                [115, 542],
                [128, 565],
                [328, 579],
                [463, 543],
                [589, 567],
                [646, 591],
                [1191, 533],
                [748, 174],
                [694, 179],
                [693, 216],
                [739, 229],
                [739, 283],
                [693, 400],
                [707, 470],
                [520, 481],
                [493, 470],
                [492, 324],
            ],
            "5S": True,
            "Yelek": True,
            "contour_threshold": 2000,
        },
        {
            "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.15:554/Streaming/Channels/1/",
            "CameraId": "2",
            "Poly": [
                [101, 580],
                [257, 505],
                [231, 385],
                [326, 361],
                [332, 267],
                [520, 210],
                [781, 143],
                [776, 259],
                [805, 283],
                [841, 295],
                [834, 344],
                [926, 388],
                [987, 303],
                [1051, 325],
                [972, 409],
                [865, 713],
                [837, 715],
                [839, 657],
                [589, 654],
                [588, 706],
                [340, 706],
                [349, 652],
                [50, 657],
            ],
            "5S": True,
            "Yelek": True,
            "contour_threshold": 2000,  # contour threshold
            # "Poly": np.array([[490, 205], [159, 565], [394, 591], [776, 591], [1161, 534], [769, 208], [699, 223]]).reshape(-1,1,2)
        },
           {
            "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.23:554/Streaming/Channels/1/",
            "CameraId": "3",
            "Poly": [
                [394, 582],
                [531, 519],
                [562, 576],
                [676, 632],
                [738, 591],
                [808, 519],
                [721, 488],
                [714, 440],
                [831, 381],
                [1024, 417],
                [1012, 452],
                [1053, 459],
                [1150, 276],
                [1225, 294],
                [1152, 650],
                [1243, 651],
                [1245, 711],
                [1015, 713],
                [1003, 662],
                [586, 657],
                [579, 707],
                [457, 708],
                [466, 648],
            ],
            "5S": True,
            "Yelek": False,
            "contour_threshold": 2000,  # contour threshold

        },
        {
            "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.6:554/Streaming/Channels/1/",
            "CameraId": "4",
            "Poly": [
                [307, 546],
                [727, 240],
                [789, 254],
                [931, 273],
                [931, 249],
                [1158, 288],
                [1273, 362],
                [1275, 561],
                [1272, 716],
                [975, 711],
                [975, 650],
                [690, 645],
                [672, 698],
                [343, 705],
                [352, 648],
            ],
            "5S": True,
            "Yelek": False,
            "contour_threshold": 2000,  # contour threshold
        }
    ]
}


# cameras_data = {
#     "1": [
#         {
#             "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.5:554/Streaming/Channels/1/",
#             "CameraId": "1",
#             "Poly": [
#                 [534, 293],
#                 [489, 267],
#                 [497, 220],
#                 [534, 209],
#                 [543, 185],
#                 [483, 184],
#                 [115, 542],
#                 [128, 565],
#                 [328, 579],
#                 [463, 543],
#                 [589, 567],
#                 [646, 591],
#                 [1191, 533],
#                 [748, 174],
#                 [694, 179],
#                 [693, 216],
#                 [739, 229],
#                 [739, 283],
#                 [693, 400],
#                 [707, 470],
#                 [520, 481],
#                 [493, 470],
#                 [492, 324],
#             ],
#             "5S": True,
#             "Yelek": True,
#             "contour_threshold": 5000,
#         },
#         {
#             "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.15:554/Streaming/Channels/1/",
#             "CameraId": "2",
#             "Poly": [
#                 [101, 580],
#                 [257, 505],
#                 [231, 385],
#                 [326, 361],
#                 [332, 267],
#                 [520, 210],
#                 [781, 143],
#                 [776, 259],
#                 [805, 283],
#                 [841, 295],
#                 [834, 344],
#                 [926, 388],
#                 [987, 303],
#                 [1051, 325],
#                 [972, 409],
#                 [865, 713],
#                 [837, 715],
#                 [839, 657],
#                 [589, 654],
#                 [588, 706],
#                 [340, 706],
#                 [349, 652],
#                 [50, 657],
#             ],
#             "5S": True,
#             "Yelek": True,
#             "contour_threshold": 5000,  # contour threshold
#             # "Poly": np.array([[490, 205], [159, 565], [394, 591], [776, 591], [1161, 534], [769, 208], [699, 223]]).reshape(-1,1,2)
#         },
#         {
#             "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.23:554/Streaming/Channels/1/",
#             "CameraId": "3",
#             "Poly": [
#                 [394, 582],
#                 [531, 519],
#                 [562, 576],
#                 [676, 632],
#                 [738, 591],
#                 [808, 519],
#                 [721, 488],
#                 [714, 440],
#                 [831, 381],
#                 [1024, 417],
#                 [1012, 452],
#                 [1053, 459],
#                 [1150, 276],
#                 [1225, 294],
#                 [1152, 650],
#                 [1243, 651],
#                 [1245, 711],
#                 [1015, 713],
#                 [1003, 662],
#                 [586, 657],
#                 [579, 707],
#                 [457, 708],
#                 [466, 648],
#             ],
#             "5S": True,
#             "Yelek": False,
#         },
#         {
#             "ConnectionStr": "rtsp://admin:Welc0me12@192.168.1.6:554/Streaming/Channels/1/",
#             "CameraId": "4",
#             "Poly": [
#                 [307, 546],
#                 [727, 240],
#                 [789, 254],
#                 [931, 273],
#                 [931, 249],
#                 [1158, 288],
#                 [1273, 362],
#                 [1275, 561],
#                 [1272, 716],
#                 [975, 711],
#                 [975, 650],
#                 [690, 645],
#                 [672, 698],
#                 [343, 705],
#                 [352, 648],
#             ],
#             "5S": True,
#             "Yelek": False,
#         }
#         # Add more camera entries if needed...
#     ]
# }
