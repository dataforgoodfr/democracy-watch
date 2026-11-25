export function useApi() {
  const config = useRuntimeConfig()
  const serverUrl = import.meta.server ? config.api.url : ''
  return $fetch.create({ baseURL: serverUrl || config.public.api.url })
}
