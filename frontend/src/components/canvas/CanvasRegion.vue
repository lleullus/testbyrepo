<script setup lang="ts">
import CompositionCanvas from './CompositionCanvas.vue'
</script>

<template>
  <div class="canvas-region-inner">
    <CompositionCanvas />
  </div>
</template>

<style scoped>
.canvas-region-inner {
  width: 100%;
  height: 100%;
  display: block;
  overflow: auto;
  padding: 16px;
  overscroll-behavior: contain;
}
</style>
