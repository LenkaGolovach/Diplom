<template>
  <div class="column">
    <div 
      class="color-stripe"
      :style="{ backgroundColor: column.color }"
    ></div>
    <div class="column-header">
      <div
        v-if="!isEditing"
        class="column-title"
        @dblclick="startEditing"
      >
        {{ column.name }}
      </div>
      <input
        v-else
        ref="titleInput"
        v-model="column.name"
        @blur="stopEditing"
        @keyup.enter="stopEditing"
        class="column-title-input"
      />
      <button class="delete-column-button" @click="deleteColumn">
        ×
      </button>
    </div>
    
    <draggable
      v-model="tasks"
      group="tasks"
      class="tasks"
      item-key="id"
      @change="onTaskChange" <!-- Добавляем обработчик изменения -->
    >
      <template #item="{ element }">
        <Task :task="element" @click="$emit('openTaskModal', element)" />
      </template>
    </draggable>

    <button class="add-task-button" @click="addTask">
      + Добавить задачу
    </button>
  </div>
</template>

<script>
import Task from './Task.vue';
import draggable from 'vuedraggable';

export default {
  components: {
    Task,
    draggable,
  },
  props: {
    column: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      tasks: this.column.tasks,
      isEditing: false,
    };
  },
  watch: {
    // Следим за изменениями задач и обновляем родительский компонент
    tasks(newTasks) {
      this.$emit('update-tasks', newTasks);
    },
  },
  methods: {
    startEditing() {
      this.isEditing = true;
      this.$nextTick(() => {
        this.$refs.titleInput.focus();
      });
    },
    stopEditing() {
      this.isEditing = false;
      this.$emit('update-column', this.column);
    },
    addTask() {
      this.$emit('add-task');
    },
    deleteColumn() {
      this.$emit('delete-column');
    },
    onTaskChange() {
      // При изменении задач (перетаскивании) обновляем родительский компонент
      this.$emit('update-tasks', this.tasks);
    },
  },
};
</script>

<style scoped>
.column {
  background: #f5f6f8;
  border-radius: 8px;
  width: 280px;
  margin: 0 12px;
  padding: 12px;
  position: relative;
}

.color-stripe {
  height: 4px;
  border-radius: 2px 2px 0 0;
  margin: -12px -12px 12px -12px;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.column-title {
  font-weight: 600;
  font-size: 15px;
  padding: 8px;
  cursor: pointer;
  border-radius: 4px;
  flex: 1;
}

.column-title:hover {
  background: #ecedf0;
}

.column-title-input {
  font-weight: 600;
  font-size: 15px;
  width: 100%;
  padding: 8px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  outline: none;
}

.delete-column-button {
  background: none;
  border: none;
  color: #5e6c84;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  margin-left: 8px;
  border-radius: 4px;
}

.delete-column-button:hover {
  background: #e0e0e0;
}

.tasks {
  min-height: 40px;
}

.add-task-button {
  width: 100%;
  padding: 8px;
  border: none;
  background: none;
  color: #5e6c84;
  cursor: pointer;
  border-radius: 4px;
  margin-top: 8px;
}

.add-task-button:hover {
  background: #ecedf0;
}
</style>