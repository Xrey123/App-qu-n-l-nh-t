from products import them_sanpham, tim_sanpham

# Test nhap kho logic
print("Testing nhap kho logic...")

# Lay thong tin san pham hien tai
ten = "PLC RACER 2T 1 lit"
res = tim_sanpham(ten)

if res:
    sp = res[0]
    print(f"\nSan pham: {sp[1]}")
    print(f"Gia le: {sp[2]}")
    print(f"Gia buon: {sp[3]}")
    print(f"Gia VIP: {sp[4]}")
    print(f"Ton kho cu: {sp[5]}")
    print(f"Nguong buon: {sp[6]}")

    # Gia su nhap them 5 san pham
    so_luong_nhap = 5
    print(f"\nNhap them: {so_luong_nhap}")

    # them_sanpham se tu dong cong them vao ton kho
    # success = them_sanpham(sp[1], sp[2], sp[3], sp[4], so_luong_nhap, sp[6])
    # print(f"Ket qua: {success}")

    print("\nTest completed (comment out them_sanpham for safety)")
else:
    print(f"San pham '{ten}' khong ton tai")
