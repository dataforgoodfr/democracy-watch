<template>
  <div class="flex min-h-screen flex-col bg-(--dw-fond-page)">
    <AppHeader />
    <main class="mx-auto w-full max-w-360 flex-1 px-4 py-8 md:px-10">
      <slot />
    </main>
  </div>
</template>
