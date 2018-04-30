Vue.component('doubt-list', {
  props: ['doubts', 'task_id', 'current_doubt', 'task_typ'],
  template: `
        <el-table
        :data="doubts"
        :cell-style="{height: '20px'}"
        highlight-current-row
        @current-change="handleCurrentChange"
        style="width: 100%"
        max-height="200">
        <el-table-column
          fixed
          prop="id"
          label="ID"
          width="50">
        </el-table-column>
        <el-table-column
          prop="doubt_text"
          label="存疑文本"
          width="170">
        </el-table-column>
        <el-table-column
          prop="doubt_comment"
          label="存疑理由"
          width="220">
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button v-if="task_typ!=11"
              @click.native.prevent="deleteRow(scope.$index, doubts)"
              type="text"
              size="small">
              移除
            </el-button>
            <el-button v-else v-show="!scope.row.processed"
              @click.native.prevent="processRow(scope.$index, doubts)"
              type="text"
              size="small">
              完成处理
            </el-button>

          </template>
        </el-table-column>
      </el-table>
    `,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_doubt', val);
    },
    deleteRow(index, rows) {
      axios.delete('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/delete/').then(function (response) {
        this.$delete(this.doubts, index)
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });


    },
    processRow(index, rows) {
      rows[index].processed = true;
      axios.put('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/', {
        task: this.task_id,
        processed: true
      }).then(function (response) {
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
    loadDoubtSeg(){
      axios.get('/api/doubt_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
        this.$emit('update:doubts', _.reverse(response.data.models))
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    }
  },
  mounted() {
    this.loadDoubtSeg();
  }
})
