<template>
  <BoardList v-if="!$route.params.id" />
  <Board v-else :id="$route.params.id" />
</template>

<script>
import BoardList from '../components/BoardList.vue'
import Board from '../components/Board.vue'

export default {
  components: {
    BoardList,
    Board
  }
}
</script>
