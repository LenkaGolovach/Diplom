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
      @change="onTaskChange"
    >
      <template #item="{ element }">
        <Task 
          :task="element" 
          @click="$emit('openTaskModal', element)"
          @delete="deleteTask(element)"
        />
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
import axios from 'axios';

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
    async deleteTask(task) {
      try {
        await axios.delete(`/api/tasks/${task.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        
        // Удаляем задачу из локального состояния
        const index = this.tasks.findIndex(t => t.id === task.id);
        if (index !== -1) {
          this.tasks.splice(index, 1);
        }
      } catch (error) {
        console.error('Ошибка удаления:', error);
      }
    },
    async onTaskChange(event) {
      // Если задача была перемещена из одной колонки в другую
      if (event.added) {
        const task = event.added.element;
        try {
          const newOrder = this.tasks.length - 1;
          
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: newOrder
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка добавления задачи в колонку:', error);
        }
      }
      // Если задача была перемещена внутри колонки
      else if (event.moved) {
        const task = event.moved.element;
        try {
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: event.moved.newIndex
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка перемещения задачи:', error);
        }
      }
      
      // Если задача была добавлена из другой колонки
      if (event.added) {
        const task = event.added.element;
        try {
          await axios.patch(`/api/tasks/${task.id}/`, {
            column: this.column.id,
            order: event.added.newIndex
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          });
          this.$emit('update-tasks', this.tasks);
        } catch (error) {
          console.error('Ошибка добавления задачи в колонку:', error);
        }
      }
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