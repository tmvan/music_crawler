# -*- encoding: utf-8 -*-

import pack

arr = [\
	[1, "Trần A,Vũ B (Group 01)", "Toán,Tiếng Anh"], \
	[2, "Nguyễn C", "Sử,Địa,Hoá"], \
	[3, "Lê D", ["Văn","Tiếng Anh"]], \
]

pack.write_csv("test_file", arr)
pack.write_csv("test_file2", arr, ["id", "name", "subjects"])
