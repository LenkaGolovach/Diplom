<template>
  <div class="board-list">
    <h1>My Boards</h1>
    <div class="boards">
      <div 
        v-for="board in boards" 
        :key="board.id" 
        class="board-item"
        @click="$router.push(`/board/${board.id}`)"
      >
        {{ board.name }}
      </div>
    </div>
    <button @click="showCreateModal = true">New Board</button>
    
    <div v-if="showCreateModal" class="modal">
      <div class="modal-content">
        <input v-model="newBoardName" placeholder="Board Name">
        <button @click="createBoard">Create</button>
        <button @click="showCreateModal = false">Cancel</button>
      </div>
    </div>
  </div>
</template>

<script>
import { toast } from 'vue-toastification';

export default {
  data() {
    return {
      boards: [],
      showCreateModal: false,
      newBoardName: ''
    };
  },
  async created() {
    await this.fetchBoards();
  },
  methods: {
    async fetchBoards() {
      try {
        const response = await fetch('http://localhost:8000/api/boards/');
        this.boards = await response.json();
      } catch (error) {
        toast.error('Failed to load boards');
      }
    },
    async createBoard() {
      if (!this.newBoardName.trim()) {
        toast.error('Board name cannot be empty');
        return;
      }

      try {
        const response = await fetch('/api/boards/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: this.newBoardName })
        });

        if (!response.ok) {
          throw new Error('Failed to create board');
        }

        const newBoard = await response.json();
        this.boards.push(newBoard);
        this.showCreateModal = false;
        this.newBoardName = '';

        // Перенаправляем на новую доску
        this.$router.push(`/board/${newBoard.id}`);
        toast.success('Board created successfully');
      } catch (error) {
        toast.error('Failed to create board');
      }
    }
  }
};
</script>

<style scoped>
.board-list {
  padding: 20px;
}

.boards {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.board-item {
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  cursor: pointer;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 5px;
}
</style>