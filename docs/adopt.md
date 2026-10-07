# นำ pod kit ไปใช้กับ project อื่น

เอกสารนี้อธิบายการนำวิธีทำงาน SuperBiz x SuperDev ไปใช้กับ project ที่มีอยู่แล้ว ไม่จำกัด stack
ทำตามลำดับ 9 ขั้น และใช้ checklist ท้ายเอกสารเพื่อตรวจว่าครบ

## 1. ประเมินว่า project เหมาะหรือไม่

pod เหมาะกับงานที่
- แบ่งเป็น change ขนาดเล็กได้ แต่ละ change ส่งมอบได้ภายในไม่กี่วัน
- มีผู้ตัดสินใจฝั่งธุรกิจหนึ่งคน (SuperBiz) และผู้ดูแลเทคนิคหนึ่งคน (SuperDev) ที่ทำงานร่วมกันได้ทุกวัน
- มี test อัตโนมัติ หรือพร้อมเริ่มเขียน test ก่อนโค้ด
- ผลกระทบเมื่อผิดพลาดย้อนกลับได้ เช่น revert แล้วระบบกลับสู่สถานะเดิม

งานที่ควรส่งให้ทีมเต็มแทน pod
- งานที่ต้องตัดสินใจร่วมกันหลายทีม หรือมีผู้มีส่วนได้ส่วนเสียหลายฝ่าย
- migration ข้อมูลขนาดใหญ่ หรือการเปลี่ยนที่ย้อนกลับไม่ได้
- งานด้านความปลอดภัย การยืนยันตัวตน การเงิน หรือข้อมูลส่วนบุคคลที่ยังไม่มีผู้เชี่ยวชาญตรวจ
- งานวิจัยที่ยังไม่ทราบว่าจะได้ผลลัพธ์แบบใด

หาก project อยู่ระหว่างกลาง ให้เริ่มจากงานความเสี่ยงต่ำก่อน และให้งานกลุ่มหลังเป็น `Risk: high` เสมอ

## 2. ติดตั้ง

ต้องมี: git, Python 3.10 ขึ้นไป, make และ Claude Code ตัวติดตั้งไม่ใช้ network

```bash
git clone git@github.com:hx-natthawat/workshop-ai-sdlc.git ~/adlc-kit
cd ~/my-project                     # repo ของ project ที่มีอยู่แล้ว
~/adlc-kit/pod/scripts/pod-install.sh .
```

ตัวเลือก
- `--with-sample` คัดลอกแอปตัวอย่าง (`app/`, `tests/test_orders.py`, `logs/`) สำหรับ repo ฝึกอบรม
- `--vendor-plugins` คัดลอก `plugins/` ลงใน repo (ใช้เมื่อไม่ติดตั้ง plugin จาก GitHub)
- `--force` เขียนทับไฟล์ที่มีอยู่แล้ว โดยเก็บไฟล์เดิมเป็น `<ไฟล์>.pod-bak`

ไฟล์ที่ติดตั้ง

| ไฟล์ | หน้าที่ |
|---|---|
| `pod.yml` | สมาชิก pod, บัญชี GitHub, WIP limit, ค่า auto-merge และ stack ของ project |
| `pod.mk` | คำสั่ง `pod-setup`, `pod-test`, `pod-strength`, `pod-check`, `pod-metrics` |
| `Makefile` | สร้างเฉพาะเมื่อ project ยังไม่มี โดย include `pod.mk` และตั้งชื่อย่อ setup, test, check |
| `AGENTS.md` | เพิ่มส่วน `<!-- pod:begin -->` ถึง `<!-- pod:end -->` ต่อท้าย เนื้อหาเดิมไม่ถูกแก้ |
| `CLAUDE.md` | เพิ่มบรรทัด `@AGENTS.md` หนึ่งครั้ง |
| `.gitignore` | เพิ่ม `.pod/` และ `!**/skills/build/` |
| `scripts/` | gate, gate-check, new-change, release-check, auto-merge-check, pr-check, test-strength และอื่น ๆ |
| `docs/gates.md`, `docs/risk-tiers.md`, `docs/merge-by-risk.md` | กติกาของ gate, risk และสิทธิ์ merge |
| `docs/risk-paths` | path อ่อนไหว change ที่แตะ path เหล่านี้ถือเป็น high |
| `docs/test-strength.md` | test อ่อน 5 แบบ และการตั้งค่า strength |
| `docs/pod-charter.md` | ข้อตกลงของ pod ให้กรอกร่วมกันก่อนเริ่ม |
| `docs/parallel-agents.md`, `docs/credits.md` | การใช้ agent หลายตัว และที่มาของแนวคิด |
| `docs/templates/` | template ของ intent, ux-brief, spec, plan, review, acceptance |
| `docs/changes/` | ที่เก็บ change ของ pod |
| `.github/workflows/pod-gates.yml` | CI รัน `make -f pod.mk pod-check` และ `scripts/pr-check.sh` |

กติกาของตัวติดตั้ง
- ไม่เขียนทับ `Makefile`, `AGENTS.md` และ `CLAUDE.md` ในทุกกรณี
- ไฟล์อื่นที่มีอยู่แล้วและเนื้อหาต่างจาก kit จะถูกข้ามและแสดงรายการ เว้นแต่ใช้ `--force`
- หาก project มี Makefile อยู่แล้ว ตัวติดตั้งจะแสดงบรรทัด `include pod.mk` ให้เพิ่มเอง
  หากไม่เพิ่ม ให้เรียกผ่าน `make -f pod.mk <target>`
- รันซ้ำได้ การรันครั้งที่สองโดยไม่มีการเปลี่ยนแปลงจะพิมพ์ "ไม่มีการเปลี่ยนแปลง"

## 3. ตั้งค่า

1. แก้ `pod.yml`
   - ชื่อและอีเมลของ SuperBiz, SuperDev และ escalation อีเมลต้องตรงกับ `git config user.email` ของแต่ละคน
   - บัญชี GitHub (`superbiz_github`, `superdev_github`, `escalation_github`)
   - stack: ตัวติดตั้งตั้งค่าให้ตามไฟล์ที่พบ ให้ตรวจอีกครั้ง

     | stack | `test_cmd` | `code_dirs` | `tests_dir` | `strength` |
     |---|---|---|---|---|
     | Node (package.json) | `npm test` | `src` | `tests`, `__tests__` หรือ `test` | `off` |
     | Python | `python3 -m unittest discover -s tests -t . -v` | package บนสุด หรือ `src` | `tests` | `python` |
     | Go (go.mod) | `go test ./...` | `.` | `tests` | `off` |
     | ไม่ทราบ | ค่าเริ่มต้นแบบ Python และแสดงคำเตือน | | | |

   - test ที่ไม่มีให้รัน (exit 5 ของ unittest และ pytest) ถือว่าผ่านเฉพาะเมื่อยังไม่มี change ใน `docs/changes/`
   - `strength: off` ทำให้ auto-merge-check ตอบ DENY เสมอ ดู `docs/test-strength.md`
2. แก้ `docs/risk-paths` ให้ตรงกับ path อ่อนไหวของ project เช่น โค้ดการชำระเงิน การยืนยันตัวตน และ migration
3. รัน `scripts/sync-codeowners.sh` เพื่อสร้าง `.github/CODEOWNERS`
4. รัน `make -f pod.mk pod-setup` แล้ว `make -f pod.mk pod-check` ต้องผ่าน
5. project ที่ไม่ใช่ Python: เพิ่ม step ติดตั้ง stack ใน `.github/workflows/pod-gates.yml` ก่อน step `pod-check`
6. ตั้งค่า GitHub: `scripts/setup-github.sh <owner/repo>` เพื่อดูแผน แล้วรันซ้ำพร้อม `--yes`
   คำสั่งนี้เปิด auto-merge ของ repo และป้องกัน branch main (ต้องผ่าน check `pod-gates` และ review จาก code owner)
7. กรอก `docs/pod-charter.md` ร่วมกัน แล้ว commit ทั้งหมดผ่าน PR

## 4. ติดตั้ง plugin (ทำทีละคน)

plugin ติดตั้งจาก GitHub โดยตรง repo ของ kit เป็น marketplace ชื่อ `adlc-pod`

```
/plugin marketplace add hx-natthawat/workshop-ai-sdlc
/plugin install superbiz@adlc-pod     # เครื่องของ SuperBiz
/plugin install superdev@adlc-pod     # เครื่องของ SuperDev
```

- repo นี้เป็น private ผู้ติดตั้งต้องมีสิทธิ์อ่าน repo บน GitHub และตั้งค่า git credential ไว้แล้ว
  (ตรวจได้ด้วย `git ls-remote git@github.com:hx-natthawat/workshop-ai-sdlc.git`)
- plugin ทำงานกับไฟล์ของ project ผ่าน `CLAUDE_PROJECT_DIR` hook จะไม่บล็อกงานใน project ที่ไม่มี `pod.yml`
  และจะพิมพ์หมายเหตุหนึ่งบรรทัด "ไม่พบ pod kit ใน project นี้"
- อัปเดต plugin เมื่อ kit ออกเวอร์ชันใหม่: `/plugin marketplace update adlc-pod`
- ทางเลือกที่ไม่ติดตั้งถาวร: ติดตั้งด้วย `--vendor-plugins` แล้วใช้ `claude --plugin-dir ./plugins/superdev`

## 5. change แรกแบบนำร่อง

- เลือกงาน `Risk: low` ที่ไม่แตะ path ใน `docs/risk-paths` และส่งมอบได้ภายในหนึ่งถึงสองวัน
- คง `auto_merge: off` ไว้ ทุก change ต้องมีมนุษย์ลงชื่อก่อน merge
- เดินครบ 4 gate ตาม README ของ kit: `scripts/new-change.sh <slug>` แล้ว intent, spec, plan, test-first, build, review, acceptance
- จดเวลาที่ติดขัดและกฎที่ไม่ชัด เพื่อปรับในขั้นที่ 8

## 6. บันไดความไว้วางใจ: เมื่อใดจึงเปิด `auto_merge: low`

เปิดเมื่อครบทุกข้อ
- pod ปิด change ครบ `auto_merge_min_track` ชิ้น (ค่าเริ่มต้น 10) ติดกันโดยไม่มี revert
- `strength` เป็น `python` หรือ `cmd` (auto-merge ต้องมีผลวัด test-strength)
- `make -f pod.mk pod-check` ผ่านใน CI ทุก PR และ branch protection เปิดแล้ว
- SuperBiz และ SuperDev ตกลงร่วมกัน และ escalation อนุมัติ เพราะ pod.yml อยู่ใน `docs/risk-paths`

เมื่อมีการ revert ใน change ล่าสุด auto-merge-check จะตอบ DENY จนกว่าจะสะสมผลงานใหม่ครบ
งาน medium และ high ไม่ merge อัตโนมัติไม่ว่าอยู่ขั้นใด

## 7. วัดผลที่ 30, 60 และ 90 วัน

ใช้ `scripts/metrics.sh docs/changes/NNN-slug` (หรือ `make -f pod.mk pod-metrics CHANGE=...`) กับทุก change ที่ปิดแล้ว

| ตัวชี้วัด | ที่มา | 30 วัน | 60 วัน | 90 วัน |
|---|---|---|---|---|
| lead time จาก intent ถึง gate 4 | metrics.sh | ค่าฐาน | ลดลง | คงที่ |
| เวลารอที่แต่ละ gate | metrics.sh | หา gate ที่รอนานที่สุด | แก้ gate นั้น | |
| จำนวน change ที่ปิดได้ | `docs/changes/` | | | |
| จำนวน revert | `event=revert` ใน gates.log | | | ไม่เพิ่มขึ้น |
| สัดส่วน change ที่ merge อัตโนมัติ | `role=auto` ใน gates.log | 0 | | |

ทบทวนตัวเลขร่วมกันทุกช่วง และบันทึกการตัดสินใจไว้ใน `docs/pod-charter.md`

## 8. ปรับ kit ให้เป็นของทีม

- กฎที่ถูกฝ่าซ้ำ 2 ครั้ง ต้องย้ายจากคำแนะนำใน skill ไปเป็น hook, script หรือ CI check
  และบันทึกการย้ายใน `docs/pod-charter.md`
- กฎเฉพาะของทีมให้เขียนใน `AGENTS.md` นอกส่วน `<!-- pod:begin -->` ถึง `<!-- pod:end -->`
- เมื่อแก้ plugin ใน repo ของ kit ให้เพิ่ม `version` ใน `plugins/<ชื่อ>/.claude-plugin/plugin.json`
  และ `metadata.version` ใน `.claude-plugin/marketplace.json` แล้วรัน `claude plugin validate --strict`
  ผู้ใช้จะได้รับเวอร์ชันใหม่เมื่อรัน `/plugin marketplace update adlc-pod`

## 9. อัปเดต kit จากต้นฉบับ

```bash
cd ~/adlc-kit && git pull
cd ~/my-project && git switch -c chore/pod-kit-update
~/adlc-kit/pod/scripts/pod-install.sh .
git status && git diff
```

- ไฟล์ที่เนื้อหาตรงกับ kit แล้วจะไม่เปลี่ยน ส่วนของ pod ใน `AGENTS.md` จะถูกแทนที่ด้วยฉบับใหม่
- ไฟล์ที่ทีมแก้เองจะถูกข้ามและแสดงรายการ ให้เทียบกับ kit ด้วย
  `diff ~/adlc-kit/pod/<ไฟล์> <ไฟล์>` แล้วตัดสินว่าจะรวมการเปลี่ยนแปลงเองหรือใช้ `--force`
- เมื่อใช้ `--force` ให้ตรวจ `git diff` และไฟล์ `.pod-bak` ทุกไฟล์ แล้วลบไฟล์ `.pod-bak` ก่อน commit
- `pod.yml` ที่มีอยู่แล้วไม่ถูกแก้ (เว้นแต่ใช้ `--force`) หาก kit เพิ่ม key ใหม่ ค่าเริ่มต้นจะถูกใช้จนกว่าทีมจะเพิ่ม key นั้นเอง
- การอัปเดตแตะ `scripts/**` และ `.github/**` ซึ่งอยู่ใน `docs/risk-paths` จึงเป็น change ระดับ high

## Checklist

- [ ] ประเมินแล้วว่างานของ project เหมาะกับ pod และกำหนดงานที่ต้องส่งทีมเต็ม
- [ ] clone kit และรัน `pod-install.sh` แล้ว ตรวจรายการไฟล์ที่ถูกข้าม
- [ ] Makefile เดิมมีบรรทัด `include pod.mk` หรือทีมตกลงใช้ `make -f pod.mk`
- [ ] `pod.yml`: ชื่อ อีเมล บัญชี GitHub และ stack ถูกต้อง
- [ ] `docs/risk-paths` ตรงกับ path อ่อนไหวของ project
- [ ] `scripts/sync-codeowners.sh` รันแล้ว และ `.github/CODEOWNERS` ถูก commit
- [ ] `make -f pod.mk pod-check` ผ่านบนเครื่องและใน CI
- [ ] CI ติดตั้ง stack ของ project ก่อน `pod-check` (project ที่ไม่ใช่ Python)
- [ ] `scripts/setup-github.sh <owner/repo>` ตรวจแผนแล้ว และรันพร้อม `--yes`
- [ ] `docs/pod-charter.md` กรอกครบ
- [ ] SuperBiz ติดตั้ง `superbiz@adlc-pod` และ SuperDev ติดตั้ง `superdev@adlc-pod`
- [ ] change แรก `Risk: low` ผ่าน 4 gate โดย `auto_merge: off`
- [ ] กำหนดวันทบทวนผลที่ 30, 60 และ 90 วัน
- [ ] ตกลงเงื่อนไขการเปิด `auto_merge: low` และผู้มีสิทธิ์เปลี่ยนค่า
