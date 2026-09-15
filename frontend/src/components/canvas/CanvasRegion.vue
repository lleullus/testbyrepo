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
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
}
</style>
