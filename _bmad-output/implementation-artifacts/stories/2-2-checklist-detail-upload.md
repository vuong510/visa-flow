---
status: done
baseline_commit: NO_VCS
---

# Story 2.2 — Checklist Item Detail & Upload Trigger

## Story
**As a** user,
**I want** to tap a checklist item and see detailed requirements,
**so that** I understand exactly what each document needs to contain.

## Acceptance Criteria
- [x] Tapping a checklist item opens BottomSheet
- [x] BottomSheet shows 3 sections: YÊU CẦU / ĐỊNH DẠNG / TẠI SAO CẦN
- [x] BottomSheet has "Tải lên tài liệu này" CTA button
- [x] Tapping CTA triggers file input click for that doc type
- [x] BottomSheet closes via onClose (X button or backdrop)
- [x] DocumentItem component shows item name, truncated description, StatusChip

## Tasks/Subtasks
- [x] Create `components/DocumentItem.jsx` with name, description, StatusChip, upload button
- [x] Create `components/StatusChip.jsx` with 7 variants
- [x] Wire selectedItem state in ChecklistScreen
- [x] Render BottomSheet conditionally with `open={true}` when item selected
- [x] Wire "Tải lên" button in BottomSheet to `triggerUpload(item.id)`
- [x] `e.stopPropagation()` on DocumentItem upload button to not trigger detail sheet

## Dev Notes
- CRITICAL: BottomSheet requires `open={true}` as explicit prop — component checks `if (!open) return null`
- selectedItem drives BottomSheet content; null = closed
- triggerUpload(docId) sets activeUploadId then calls fileInputRef.current.click()
- Hidden `<input type="file">` with onChange={handleFileSelected}

## Dev Agent Record

### Completion Notes
BottomSheet detail sheet working. Fixed open prop bug.

### Debug Log
- Bug: BottomSheet never opened — was rendering `<BottomSheet title={...}>` without `open={true}`. Added `open={true}` to fix.

## File List
- `visa-client/src/components/DocumentItem.jsx`
- `visa-client/src/components/StatusChip.jsx`
- `visa-client/src/screens/ChecklistScreen.jsx` (selectedItem + BottomSheet wiring)

## Change Log
- 2026-06-29: Story completed; open prop bug fixed

## Status
Done
