<template>
  <div class="card-head">
    <h3>{{ title }}</h3>
    <div class="toolbar-inline">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>
