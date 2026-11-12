/** Rung nhẹ khi bấm nút (Android; iPhone không hỗ trợ và sẽ bỏ qua). */
export function buzz(ms = 12) {
  try {
    navigator.vibrate?.(ms);
  } catch {
    /* không hỗ trợ */
  }
}
