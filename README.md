# Tripod

แนวปฏิบัติสำหรับทีมส่งมอบขนาดเล็กที่ทำงานร่วมกับ AI agent ชื่อมาจากสามขาที่ทำให้ทีมยืนได้มั่นคง

| ขา | บทบาทที่รวมไว้ | สถานะ |
|---|---|---|
| **SuperBiz** | PO, PM, BA, Designer: ทำอะไรและเพราะอะไร | ใช้งานได้ |
| **SuperDev** | SA, Dev, QA, Deploy, MA: ทำอย่างไรและปลอดภัยหรือไม่ | ใช้งานได้ |
| **SuperCEO** | ทิศทาง ลำดับความสำคัญ และการอนุมัติงานความเสี่ยงสูง | แผนในอนาคต ตอนนี้ใช้บทบาท escalation ใน `pod.yml` แทน |

ใช้ใน workshop ภาคปฏิบัติ 2 วัน เรื่อง Agentic Development Lifecycle (ADLC) ของ HarmonyX
และนำไปติดตั้งใน project อื่นได้

## นำไปใช้กับ project อื่น

ติดตั้ง kit ลงใน repo ที่มีอยู่แล้วได้ทุก stack ตัวติดตั้งไม่เขียนทับ Makefile, AGENTS.md และ CLAUDE.md และรันซ้ำได้

```bash
gh repo clone feronera/tripod ~/tripod
cd ~/my-project && ~/tripod/scripts/pod-install.sh .
```

ติดตั้ง plugin ทีละคนจาก GitHub (repo เป็น private ผู้ติดตั้งต้องมีสิทธิ์อ่าน repo และตั้งค่า git credential แล้ว)

```
/plugin marketplace add feronera/tripod
/plugin install superbiz@tripod     # หรือ superdev@tripod
```

ขั้นตอนครบ 9 ขั้นและ checklist อยู่ใน [docs/adopt.md](docs/adopt.md)

- **SuperBiz** รับบทบาท PO, PM, BA และ Designer รับผิดชอบว่า "ทำอะไรและเพราะอะไร"
- **SuperDev** รับบทบาท SA, Dev, QA, Deploy และ MA (ดูแลระบบ) รับผิดชอบว่า "ทำอย่างไรและปลอดภัยหรือไม่"

agent ร่างงานของทุกบทบาท มนุษย์ตัดสินใจที่ gate 4 จุด
หลัก "ผู้เขียนและผู้อนุมัติเป็นคนละคน" รักษาไว้ด้วย cross-gate

| Gate | Artifact | Owner อนุมัติ | อีกคนตรวจทาน (cross) |
|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev (ทำได้จริงและวัดผลได้หรือไม่) |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev |
| 3 | plan.md | SuperDev | SuperBiz (ยังตรงกับ intent หรือไม่) |
| 4 | PR / acceptance.md | SuperDev (โค้ด) | SuperBiz (ยอมรับตาม Success measure) |

กฎเพิ่มเติม
- **Risk tier:** ระบุใน intent.md (`Risk: low | medium | high`) งาน `high` ต้องมี escalation ลงชื่อเพิ่มที่ gate 2 และ 4 ดู `docs/risk-tiers.md`
- **WIP limit:** change ที่ผ่าน gate 1 แต่ยังไม่ผ่าน gate 4 เปิดพร้อมกันได้ไม่เกิน `wip_limit` ใน `pod.yml` (ค่าเริ่มต้น 2)
- **Stale approval:** การอนุมัติแต่ละครั้งเก็บ blob hash ของ artifact หาก artifact ถูกแก้หลังอนุมัติ gate-check จะไม่ผ่าน
- **Merge ตาม risk:** gate 4 แยกเป็น merge-ready และ release-ready งาน low ที่ผ่าน 9 เงื่อนไข merge อัตโนมัติได้
  งาน medium ใช้ SuperDev คนเดียว งาน high ต้องครบสามคน ดู `docs/merge-by-risk.md`

ชุดนี้มีสามชั้น
1. **Governance:** gate, cross-approval, risk tier, WIP limit และ audit log ใน `gates.log`
2. **วิธีทำงานทางวิศวกรรม** (ดัดแปลงจาก pstack ดู `docs/credits.md`): โครงข้อมูลก่อน logic,
   throughput checkpoint, งานทีละ unit ที่ตรวจได้, test ที่ตรวจพฤติกรรม, แก้ bug ที่ต้นเหตุ,
   ความเห็นที่สองจาก model อื่น และ arena สำหรับเทียบแนวทางออกแบบ
3. **การบังคับใช้:** หลักการที่สำคัญเป็นการตรวจด้วย script, hook และ CI ไม่ใช่เพียงคำแนะนำ

## เริ่มต้นใช้งาน

repo นี้เป็น template repository: สร้าง repo ใหม่ของทีมจาก template แล้วเริ่มใช้ได้ทันที

```bash
gh repo create my-pod --private --template feronera/tripod --clone && cd my-pod
# แก้ pod.yml: ใส่ชื่อและอีเมลจริงของ SuperBiz, SuperDev และ escalation
# อีเมลต้องตรงกับ git config user.email ของแต่ละคน
make setup
make check
git add -A && git commit -m "chore: start pod"
```

ต้องมี: Python 3.10 ขึ้นไป, git, make และ Claude Code ไม่ต้องติดตั้ง package เพิ่ม

`make` ในโฟลเดอร์นี้เรียก target ใน `pod.mk` (`make check` เท่ากับ `make -f pod.mk pod-check`)
คำสั่ง test และวิธีตรวจ test-strength อ่านจาก `pod.yml` (`test_cmd`, `code_dirs`, `tests_dir`, `strength`)

## ลำดับงานของหนึ่ง change

1. SuperBiz: `scripts/new-change.sh order-history` แล้วใช้ skill `/superbiz:intent` ร่าง intent.md
2. Gate 1: SuperBiz `scripts/gate.sh docs/changes/001-order-history 1` แล้ว SuperDev ตรวจทานและรันคำสั่งเดียวกัน
3. SuperBiz: `/superbiz:ux-brief` และ `/superbiz:spec` แล้วผ่าน gate 2
4. SuperDev: `/superdev:plan` (Data shape, Throughput checkpoint, Parallel parts) แล้วผ่าน gate 3
5. SuperDev: `/superdev:test-first`, `/superdev:build` และ `/superdev:review` แล้วเปิด PR
6. SuperDev: `/superdev:merge` merge ตาม risk (low อาจ merge อัตโนมัติ, medium SuperDev ลงชื่อ gate 4, high มนุษย์ครบสามคน)
7. SuperBiz: `/superbiz:acceptance` แล้วลงชื่อ gate 4 (ตรวจรับ ก่อนหรือหลัง merge ตาม risk)
8. SuperDev: `/superdev:release` (ต้องผ่าน `scripts/release-check.sh`) และ SuperBiz: `/superbiz:release-notes`

bug ใช้ `/superdev:bug-fix` และแนวทางออกแบบที่ยังตัดสินไม่ได้ใช้ `/superdev:arena`

## คำสั่ง

| คำสั่ง | ใช้ทำอะไร |
|---|---|
| `make setup` | ตรวจเครื่องมือ และเตรียมโฟลเดอร์ `.pod/` |
| `make test` หรือ `scripts/pod-test.sh` | รัน `test_cmd` ใน pod.yml (ใน kit นี้คือ unit test ของ `app/` และ scripts) |
| `make strength` หรือ `scripts/test-strength.sh` | ตามโหมด `strength` ใน pod.yml: `python` หา test ที่ยังผ่านแม้ทุกฟังก์ชันใน `code_dirs` คืนค่า None, `off` ข้าม, `cmd` รัน `strength_cmd` ดู `docs/test-strength.md` |
| `make check` | test, strength, `scripts/sync-codeowners.sh --check` และ `scripts/gate-check.sh --all` (CI รันทุก pull request) |
| `scripts/new-change.sh <slug>` | สร้าง `docs/changes/NNN-slug/intent.md` ปฏิเสธเมื่อถึง WIP limit |
| `scripts/gate.sh <change-dir> <1-4>` | ลงชื่อ gate ด้วยอีเมลจาก `git config user.email` บันทึกลง `gates.log` |
| `scripts/gate-check.sh <change-dir> [upto]` | ตรวจ gate ของ change เดียว (`4` = merge-ready ตาม risk) |
| `scripts/release-check.sh <change-dir>` | release-ready: gate 4 ครบทุกคน ไม่ stale ไม่มี revert และตรวจรับไม่เกินกำหนด |
| `scripts/auto-merge-check.sh <change-dir> [--base main] [--record]` | `ALLOW` หรือ `DENY` พร้อมเหตุผลสำหรับ merge อัตโนมัติ `--record` บันทึก `role=auto` |
| `scripts/mark-revert.sh <change-dir> "<reason>"` | มนุษย์บันทึกว่า change ถูก revert |
| `scripts/pr-check.sh [--author A --approvals B,C --base main]` | CI: ตรวจ approval บน GitHub ตาม risk จริง |
| `scripts/sync-codeowners.sh [--check]` | สร้างหรือตรวจ `.github/CODEOWNERS` จาก `docs/risk-paths` |
| `scripts/pod-install.sh <repo> [--with-sample] [--vendor-plugins] [--force]` | ติดตั้ง kit ลงใน repo อื่น ดู `docs/adopt.md` |
| `scripts/setup-github.sh <owner/repo> [--yes]` | เปิด auto-merge และป้องกัน branch main (แสดงแผนก่อน ใช้จริงเมื่อมี `--yes`) |
| `scripts/gate-check.sh --all` | ตรวจทุก change (change ที่ยังไม่มี gates.log ถือเป็น draft) |
| `scripts/metrics.sh <change-dir>` หรือ `make metrics CHANGE=<change-dir>` | เวลาจาก commit แรกของ intent.md ถึงแต่ละ gate และ lead time |
| `touch .pod/lock-tests` | ล็อก tests ไม่ให้ agent แก้ |
| `touch .pod/kill-switch` | หยุด agent ทุกตัวที่โหลด plugin superdev |

## โหลด plugin

plugin อยู่ใน repo นี้ ใช้ `--plugin-dir` โหลดเฉพาะ session โดยไม่เปลี่ยนการตั้งค่าของเครื่อง

```bash
# เครื่องของ SuperBiz
claude --plugin-dir ./plugins/superbiz

# เครื่องของ SuperDev
claude --plugin-dir ./plugins/superdev
```

หากต้องการติดตั้งแบบถาวร ใช้ marketplace ชื่อ `tripod` จาก GitHub
(`/plugin marketplace add feronera/tripod` แล้ว `/plugin install superbiz@tripod` หรือ `superdev@tripod`)
ใน repo ที่คัดลอกโฟลเดอร์นี้ไปทั้งโฟลเดอร์ ใช้ `/plugin marketplace add ./` แทนได้
hook ของ plugin ไม่บล็อกงานใน project ที่ไม่มี `pod.yml` และพิมพ์หมายเหตุว่า "ไม่พบ pod kit ใน project นี้"

| Plugin | Skills | Agents | Hooks |
|---|---|---|---|
| superbiz | intent, ux-brief, spec, acceptance, release-notes | ba-researcher, ux-critic | biz-scope: แก้ได้เฉพาะ `docs/` |
| superdev | plan, build, test-first, review, bug-fix, arena, release, incident, merge | reviewer, reviewer-second, monitor | kill-switch, protect-tests, gate-guard |

## โครงสร้าง

```
AGENTS.md, CLAUDE.md     กฎสำหรับ agent
pod.yml                  สมาชิก pod, บัญชี GitHub, WIP limit, ค่า auto-merge และ stack (test_cmd, code_dirs, tests_dir, strength)
pod.mk                   pod-setup, pod-test, pod-strength, pod-check, pod-metrics
Makefile                 include pod.mk และชื่อย่อ setup, test, strength, check, metrics
app/orders.py            โดเมนตัวอย่าง: สถานะคำสั่งซื้อของลูกค้า
tests/                   unit test ของ app และ scripts
docs/gates.md            gate และคำถามตรวจ
docs/risk-tiers.md       ระดับความเสี่ยง
docs/pod-charter.md      ข้อตกลงของ pod
docs/parallel-agents.md  ให้ agent หลายตัวทำงานพร้อมกัน และ arena
docs/merge-by-risk.md    ใคร merge ได้ในแต่ละ risk, 9 เงื่อนไข auto-merge, revert, ตั้งค่า GitHub
docs/risk-paths          path อ่อนไหว (แตะแล้วถือเป็น high)
docs/test-strength.md    test อ่อน 5 แบบ และโหมด strength (python, off, cmd)
docs/adopt.md            นำ kit ไปใช้กับ project อื่น และ checklist
docs/credits.md          ที่มาของแนวคิดที่ดัดแปลงจาก pstack
docs/templates/          intent, ux-brief, spec, plan, review, acceptance
docs/changes/            change ของ pod (NNN-slug/)
scripts/                 new-change, gate, gate-check, release-check, mark-revert, metrics, pod-test (lib.py)
                         test-strength (strength.py)
                         auto-merge-check, pr-check, sync-codeowners (merge_rules.py), setup-github
                         pod-install (pod_install.py) ติดตั้ง kit ลงใน repo อื่น
plugins/                 superbiz และ superdev
logs/sample-app.log      log สังเคราะห์สำหรับ lab incident
.github/workflows/       CI job pod-gates: make -f pod.mk pod-check และ pr-check
.github/CODEOWNERS       สร้างจาก docs/risk-paths
```

## ข้อควรรู้

- agent ไม่ลงชื่อ gate แทนมนุษย์ คำสั่ง `scripts/gate.sh` และ `scripts/mark-revert.sh` ต้องรันโดยมนุษย์เท่านั้น
  agent รัน `scripts/auto-merge-check.sh --record` และ `gh pr merge --auto --squash` ได้เฉพาะเมื่อผลเป็น `ALLOW`
- `auto_merge` ใน pod.yml เริ่มที่ `off` เปิดเป็น `low` เมื่อ pod สะสมผลงานครบ ดู `docs/pod-charter.md`
- การตั้งค่า GitHub: ใส่บัญชีใน pod.yml, `scripts/sync-codeowners.sh`, แล้ว `scripts/setup-github.sh <owner/repo> --yes`
  ผู้อนุมัติ PR ต้องไม่ใช่ผู้เปิด PR ถ้า agent เปิด PR ด้วยบัญชีของ SuperDev ระบบจะให้ SuperBiz อนุมัติแทน ดู `docs/merge-by-risk.md`
- ข้อมูลใน `app/` และ `logs/` เป็นข้อมูลสังเคราะห์ทั้งหมด
- โฟลเดอร์ `.pod/` ไม่ถูก commit (อยู่ใน `.gitignore`) เพราะเป็นสถานะของเครื่องแต่ละเครื่อง

## Credits

แนวคิดด้านวิธีทำงานหลายข้อดัดแปลงจาก pstack ของ Lauren Tan (MIT License, Copyright (c) 2026 Lauren Tan)
รายการแนวคิดที่ดัดแปลงอยู่ใน `docs/credits.md`
