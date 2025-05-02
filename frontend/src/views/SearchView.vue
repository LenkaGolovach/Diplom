<template>
  <div class="search-view">
    <h1>Поиск задач</h1>
    <SearchTasks />
  </div>
</template>

<script>
import SearchTasks from '@/components/SearchTasks.vue'

export default {
  name: 'SearchView',
  components: {
    SearchTasks
  }
}
</script>

<style scoped>
.search-view {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
  color: #333;
}
</style> 