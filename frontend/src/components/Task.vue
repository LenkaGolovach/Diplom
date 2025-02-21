<template>
  <div class="task" @click="$emit('click', task)">
    {{ task.name }}
    <button @click.stop="deleteTask">Delete</button>
  </div>
</template>

<script>
export default {
  props: {
    task: Object,
  },
  methods: {
    deleteTask() {
      this.$emit('delete');
    },
  },
};
</script>

<style scoped>
.task {
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 3px;
  background-color: #f9f9f9;
  cursor: pointer;
}
</style>
