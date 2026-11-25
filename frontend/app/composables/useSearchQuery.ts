export function useSearchQuery() {
  const route = useRoute()
  return computed(() =>
    typeof route.query.q === 'string' ? route.query.q : ''
  )
}
