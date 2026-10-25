// Ports des sites construits pendant les tests. Hors des ports de dev (3000-3010) :
// avec `reuseExistingServer`, un serveur de dev oublié serait testé à la place du build.
export const E2E_PORTS = { web: 4310, docs: 4311 } as const;
