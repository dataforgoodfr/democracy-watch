<script setup lang="ts">
  import type { TagProps } from '@/components/tag/Tag.interface'

  const props = withDefaults(defineProps<TagProps>(), {
    type: 'default'
  })

  const emit = defineEmits<{
    'update:pressed': [pressed: boolean]
    delete: []
  }>()

  const NuxtLink = resolveComponent('NuxtLink')

  const isButton = computed(
    () => props.type === 'selectable' || props.type === 'deletable'
  )
  const isInteractive = computed(() => props.type !== 'default')
  const isDisabled = computed(
    () => props.type !== 'default' && props.disabled === true
  )

  const element = computed(() => {
    if (props.type === 'clickable') return props.disabled ? 'a' : NuxtLink
    if (isButton.value) return 'button'
    return 'p'
  })

  const elementAttributes = computed(() => {
    switch (props.type) {
      case 'clickable':
        if (props.disabled) return { role: 'link', 'aria-disabled': 'true' }
        return {
          ...props.attributes,
          to: props.href,
          ...(props.blank && { target: '_blank', rel: 'noopener' })
        }
      case 'selectable':
        return {
          type: 'button',
          'aria-pressed': String(props.pressed),
          disabled: props.disabled
        }
      case 'deletable':
        return {
          type: 'button',
          'aria-label': `Retirer le filtre ${props.label}`,
          disabled: props.disabled
        }
      default:
        return {}
    }
  })

  const leftIcon = computed(() =>
    props.type !== 'deletable' && props.hasIcon ? props.icon : undefined
  )

  const isHighlighted = computed(
    () =>
      props.type === 'deletable' ||
      (props.type === 'selectable' && props.pressed)
  )

  const classes = computed(() => [
    'dw-tag',
    props.type === 'clickable' && props.accent && `dw-tag--${props.accent}`,
    {
      'dw-tag--sm': props.size === 'sm',
      'dw-tag--selectionne': isHighlighted.value,
      'cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dw-bordure-action':
        isInteractive.value && !isDisabled.value,
      'hover:bg-dw-fond-selection':
        isInteractive.value && !isHighlighted.value && !isDisabled.value,
      'cursor-not-allowed opacity-50': isDisabled.value
    }
  ])

  function handleClick() {
    if (isDisabled.value) return
    if (props.type === 'selectable') emit('update:pressed', !props.pressed)
    if (props.type === 'deletable') emit('delete')
  }
</script>

<template>
  <component
    :is="element"
    v-bind="elementAttributes"
    :class="classes"
    @click="isButton ? handleClick() : undefined"
  >
    <UIcon
      v-if="type === 'selectable' && pressed"
      name="i-lucide-check"
      class="size-4 shrink-0"
      data-testid="tag-check"
    />
    <UIcon
      v-if="leftIcon"
      :name="leftIcon"
      class="size-4 shrink-0"
      data-testid="tag-icon"
    />
    {{ label }}
    <UIcon
      v-if="type === 'deletable'"
      name="i-lucide-x"
      class="size-4 shrink-0"
      data-testid="tag-delete"
    />
  </component>
</template>
