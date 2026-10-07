# Merge ตาม risk

gate 4 แยกเป็นสองการตรวจ
- **merge-ready** (`scripts/gate-check.sh <change-dir> 4`): merge เข้า main ได้หรือไม่ hook gate-guard และ CI ใช้การตรวจนี้
- **release-ready** (`scripts/release-check.sh <change-dir>`): ปล่อยขึ้น production ได้หรือไม่

## ใครทำอะไรในแต่ละระดับ

| Risk จริง | merge-ready | ผู้ merge | approval บน GitHub (pr-check) | release-ready |
|---|---|---|---|---|
| low | owner + cross หรือบันทึก `role=auto` | agent ได้ เมื่อ `auto-merge-check` พิมพ์ ALLOW | ไม่ต้องมี เมื่อบันทึก auto ผ่าน auto-merge-check ซ้ำใน CI มิฉะนั้นต้องมี SuperDev | owner + cross (SuperBiz ตรวจรับภายใน `acceptance_hours`) |
| medium | owner (SuperDev) | SuperDev หรือ agent หลัง SuperDev ลงชื่อ | SuperDev | owner + cross |
| high | owner + cross + escalation | มนุษย์ | SuperDev, SuperBiz และ escalation | owner + cross + escalation |

- Risk จริง = Risk ใน intent.md แต่ถ้า diff แตะ path ใน `docs/risk-paths` จะถือเป็น high เสมอ
- ผู้อนุมัติบน GitHub ต้องไม่ใช่ผู้เปิด PR ถ้า agent เปิด PR ด้วยบัญชีของ SuperDev งาน low และ medium ใช้ approval ของ SuperBiz แทน (เป็นการตรวจไขว้แบบเดียวกับ cross-gate) งาน high ต้องได้ approval จากทุกคนที่ไม่ใช่ผู้เปิด PR
- PR ที่ไม่มีโฟลเดอร์ change ใช้กฎของ medium
- release-ready ต้องไม่มีบันทึก `event=revert`

## เงื่อนไข 9 ข้อของ auto-merge (`scripts/auto-merge-check.sh <change-dir> [--base main] [--record]`)

พิมพ์ `ALLOW` เมื่อผ่านครบทุกข้อ มิฉะนั้นพิมพ์ `DENY` พร้อมเหตุผลบรรทัดละข้อ

1. `pod.yml` ตั้ง `auto_merge: low`
2. Risk ใน intent.md เป็น `low` และการอนุมัติ gate 1 ยังไม่ stale (Risk ไม่ถูกลดหลังอนุมัติ)
3. ไม่มีไฟล์ใน `git diff --name-only <base>...HEAD` ที่ตรงกับ `docs/risk-paths`
4. gate 1 ถึง 3 ครบและไม่ stale
5. `review.md` มี `blockers: 0`, `second_opinion: agree` และ `reviewed_head` ตรงกับ HEAD
   (commit หลัง reviewed_head ที่แก้เฉพาะไฟล์ในโฟลเดอร์ของ change นี้ เช่น review.md ไม่นับว่าโค้ดเปลี่ยน)
6. `test_cmd` ใน pod.yml และ `scripts/test-strength.sh` ผ่าน หาก pod.yml ตั้ง `strength: off` จะ DENY เสมอ
   เพราะ merge อัตโนมัติต้องมีผลวัด test-strength (ดู `docs/test-strength.md`)
7. ไม่มีบรรทัดถูกลบใน `tests_dir` (ค่าเริ่มต้น `tests/`) เพิ่ม test ได้อย่างเดียว
8. บรรทัดที่เปลี่ยนนอก `docs/` และ `tests_dir` รวมไม่เกิน `auto_merge_max_lines`
9. change ที่ผ่าน gate 4 ล่าสุด `auto_merge_min_track` ชิ้นมีครบ และไม่มีชิ้นใดถูก revert

`--record` เมื่อได้ ALLOW จะเพิ่มบรรทัดนี้ใน gates.log

```
gate=4 role=auto by=auto-merge at=<ISO> blob=<hash ของ acceptance.md หรือ -> head=<sha>
```

agent รัน `auto-merge-check.sh --record` แล้ว `gh pr merge --auto --squash` ได้เฉพาะเมื่อพิมพ์ ALLOW
agent ไม่รัน `scripts/gate.sh` และ `scripts/mark-revert.sh`

## ตรวจรับหลัง merge

- หลังบันทึก auto SuperBiz ลงชื่อ gate 4 (cross) ได้ก่อน SuperDev แล้ว SuperDev ลงชื่อ owner ด้วย acceptance.md ฉบับเดียวกัน
- ถ้าเลย `acceptance_hours` แล้ว SuperBiz ยังไม่ลงชื่อ release-check จะพิมพ์ "ห้ามปล่อยขึ้น production จนกว่า SuperBiz ตรวจรับ"

## Revert

1. ย้อนโค้ด: `git revert <commit>` แล้วเปิด PR ตามปกติ
2. มนุษย์ในทีม (SuperBiz, SuperDev หรือ escalation) บันทึก:
   `scripts/mark-revert.sh docs/changes/NNN-slug "<เหตุผล>"`
   ซึ่งเพิ่มบรรทัด `event=revert by=<email> at=<ISO> reason="..."`
3. ผล: release-check ของ change นั้นไม่ผ่าน และ auto-merge ถูกปิดจนกว่าจะมี change ที่ไม่ถูก revert ครบ `auto_merge_min_track` ชิ้นต่อจากนั้น

## ตั้งค่า GitHub

1. ใส่บัญชี GitHub ใน `pod.yml` (`superbiz_github`, `superdev_github`, `escalation_github`)
2. `scripts/sync-codeowners.sh` เพื่อสร้าง `.github/CODEOWNERS` จาก `docs/risk-paths` แล้ว commit (`make check` ตรวจว่าตรงกัน)
3. `scripts/setup-github.sh <owner/repo>` เพื่อดูสิ่งที่จะตั้งค่า แล้วรันซ้ำพร้อม `--yes`
   - เปิด auto-merge ของ repo
   - ป้องกัน main: ต้องผ่าน check `pod-gates`, ต้องมี review จาก code owner, ยกเลิก review เก่าเมื่อมี commit ใหม่, ห้าม force push
4. CI (`.github/workflows/pod-gates.yml`) รัน `make -f pod.mk pod-check` และ `scripts/pr-check.sh` ซึ่งอ่านผู้เปิด PR และผู้ approve ด้วย `gh api`
   การ approve บน GitHub ผูกกับบัญชีที่ login จึงปลอมยากกว่าอีเมลใน git config
