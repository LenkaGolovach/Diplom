<template>
  <div class="boards-list">
    <div class="header">
      <h1>Мои доски</h1>
      <button class="add-board-button" @click="createBoard">+ Создать доску</button>
      <button class="logout-button" @click="logout">Выйти</button>
    </div>
    <div class="board-cards">
      <div
        v-for="board in boards"
        :key="board.id"
        class="board-card"
        @click="goToBoard(board.id)"
      >
        {{ board.name }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      boards: [],
    };
  },
  async created() {
    await this.fetchBoards();
  },
  methods: {
    async fetchBoards() {
      try {
        const response = await axios.get('/api/boards/', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.boards = response.data;
      } catch (error) {
        console.error('Ошибка загрузки досок:', error);
      }
    },
    async createBoard() {
      try {
        const response = await axios.post(
          '/api/boards/',
          { name: 'Новая доска' },
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );
        this.boards.push(response.data);
      } catch (error) {
        console.error('Ошибка создания доски:', error);
      }
    },
    goToBoard(boardId) {
      this.$router.push(`/boards/${boardId}`);
    },
    logout() {
      localStorage.removeItem('token');
      this.$router.push('/login');
    },
  },
};
</script>

<style scoped>
.boards-list {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.add-board-button {
  background: #0079bf;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.add-board-button:hover {
  background: #026aa7;
}

.logout-button {
  background: #eb5a46;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.logout-button:hover {
  background: #cf513d;
}

.board-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.board-card {
  background: white;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 200px;
  cursor: pointer;
}

.board-card:hover {
  background: #f5f6f8;
}
</style>