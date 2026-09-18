export const ACTIVE_CUT_COUNT_MISMATCH_MESSAGE =
  '기존 활성 컷 수와 다른 초안입니다. 먼저 컷 추가/비활성화로 구성을 명시적으로 변경하세요.'

export function resolveRebaselineCutCount(
  hasBaseline: boolean,
  activeCutCount: number,
  preferredCount?: number,
): number {
  const normalizedActiveCount =
    Number.isSafeInteger(activeCutCount) && activeCutCount >= 1
      ? activeCutCount
      : 1

  if (hasBaseline) return normalizedActiveCount

  if (
    typeof preferredCount === 'number' &&
    Number.isSafeInteger(preferredCount) &&
    preferredCount >= 1
  ) {
    return preferredCount
  }

  return normalizedActiveCount
}

export function draftGenerationErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message.trim()) {
    return error.message.trim()
  }

  if (typeof error === 'object' && error !== null && 'message' in error) {
    const message = (error as { message?: unknown }).message
    if (typeof message === 'string' && message.trim()) {
      return message.trim()
    }
  }

  if (typeof error === 'string' && error.trim()) {
    return error.trim()
  }

  return 'AI 콘티 생성 중 알 수 없는 오류가 발생했습니다. 다시 시도하거나 수동 입력을 사용하세요.'
}
