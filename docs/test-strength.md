# Test strength

test ที่ผ่านไม่ได้แปลว่าโค้ดถูก test บางแบบผ่านได้แม้โค้ดไม่ทำงานเลย เอกสารนี้อธิบาย test อ่อน 5 แบบ
วิธีที่ `scripts/test-strength.sh` ตรวจใน Python และวิธีเพิ่มการตรวจสำหรับ stack อื่น

## test อ่อน 5 แบบ

test ทั้ง 5 แบบนี้ยังผ่านได้แม้ทุกฟังก์ชันในโค้ดคืนค่าว่าง (None, null หรือ nil)

| แบบ | ตัวอย่าง | วิธีแก้ |
|---|---|---|
| 1. assert อ่อนหรือไม่มี assert | มีเพียง `assertTrue(x)`, `assertIsNotNone(x)` หรือเรียกฟังก์ชันโดยไม่ตรวจผล | assert ผลลัพธ์ด้วยค่าที่ระบุชัด |
| 2. ตรวจเฉพาะ mock หรือการไม่มีข้อมูล | มีเพียง `assertIsNone(find("x"))` หรือ `assertEqual(list_orders(), [])` | จับคู่กับกรณีที่มีข้อมูลใน test เดียวกัน |
| 3. อ้างอิงตัวเอง | `assertEqual(f(a), f(a))` ค่าที่คาดหวังมาจากโค้ดที่กำลังทดสอบ | เขียนค่าที่คาดหวังจาก spec |
| 4. ตรึงค่าคงที่ | assert ค่าคงที่หรือ config ที่เขียนไว้ในโค้ดซ้ำ | ทดสอบกลไกที่ใช้ค่านั้น |
| 5. fixture ตรวจ fixture | assert ข้อมูลที่ test สร้างเอง โดยไม่ได้เรียกโค้ดที่ทดสอบ | เรียกโค้ดจริงแล้ว assert ผลของโค้ด |

## การตั้งค่าใน pod.yml

```
test_cmd: python3 -m unittest discover -s tests -t . -v
code_dirs: app
tests_dir: tests
strength: python           # python | off | cmd
strength_cmd:
```

| `strength` | การทำงานของ `scripts/test-strength.sh` | auto-merge-check |
|---|---|---|
| `python` | ตรวจแบบ Python ตามหัวข้อถัดไป exit 1 เมื่อพบ test อ่อน | ใช้ผลการตรวจ |
| `off` | พิมพ์ข้อความว่าปิดอยู่ และ exit 0 reviewer ต้องตรวจ 5 แบบข้างต้นเอง | DENY เสมอ เพราะ merge อัตโนมัติต้องมีผลวัด strength |
| `cmd` | รัน `strength_cmd` และ exit ด้วย code ของคำสั่งนั้น | ใช้ผลของคำสั่ง |

## วิธีตรวจแบบ Python (`strength: python`)

1. หา test ใน `tests_dir` ที่ import package จาก `code_dirs`
   - โฟลเดอร์ใน `code_dirs` ที่มี `__init__.py` ถือเป็น package (`app` ให้ชื่อ `app.orders`)
   - โฟลเดอร์ที่ไม่มี `__init__.py` ถือเป็น source root (`src/shop/cart.py` ให้ชื่อ `shop.cart`)
2. รัน test แต่ละตัวตามปกติ test ที่ไม่ผ่านตั้งแต่แรกจะแสดงเป็น `FAIL (ปกติ)` และไม่นับ
3. แทนทุกฟังก์ชันใน module ใต้ `code_dirs` ด้วยฟังก์ชันที่คืนค่า None แล้วรัน test นั้นอีกครั้ง
4. test ที่ยังผ่านในรอบที่ 3 จะแสดงเป็น `WEAK <test id>` เพราะ test นั้นไม่ fail แม้โค้ดเสีย

ข้อจำกัด: ตรวจได้เฉพาะ test แบบ `unittest.TestCase` และฟังก์ชันระดับ module (ไม่รวม method ของ class)

## เพิ่มการตรวจสำหรับ stack อื่น (`strength: cmd`)

ทีมที่ใช้ stack อื่นเพิ่มการตรวจของตนเองได้ โดยเขียนคำสั่งที่ exit 1 เมื่อพบ test อ่อน แล้วตั้งค่าใน pod.yml

```
strength: cmd
strength_cmd: node scripts/strength.js
```

แนวทางเขียนคำสั่งตรวจ
1. ใช้หลักเดียวกับแบบ Python: ทำให้โค้ดคืนค่าว่างแล้วดูว่า test ใดยังผ่าน
   เช่น ใช้ mutation testing ของ stack นั้น (Stryker สำหรับ JavaScript หรือ TypeScript, go-mutesting สำหรับ Go)
   แล้วกำหนดเกณฑ์ว่า mutant ที่รอดเกินเท่าใดถือว่าไม่ผ่าน
2. พิมพ์ผลบรรทัดละหนึ่ง test ในรูป `WEAK <test id>` เพื่อให้ auto-merge-check แสดงชื่อ test ในเหตุผลได้
3. exit 0 เมื่อไม่พบ test อ่อน และ exit 1 เมื่อพบ
4. คำสั่งต้องไม่ใช้ network และรันได้ใน CI
5. เมื่อคำสั่งพร้อม ให้เปลี่ยน `strength: off` เป็น `strength: cmd` ผ่าน change ที่มี escalation
   เพราะ pod.yml อยู่ใน `docs/risk-paths`

ระหว่างที่ยังไม่มีคำสั่งตรวจ ให้ใช้ `strength: off` และ reviewer ตรวจ 5 แบบข้างต้นใน review.md
