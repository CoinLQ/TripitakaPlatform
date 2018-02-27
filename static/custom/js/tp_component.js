
Vue.component('doubt-list', {
    props: ['doubts', 'task_id', 'current_doubt'],
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
          width="150">
        </el-table-column>
        <el-table-column
          prop="doubt_text"
          label="存疑文本"
          width="120">
        </el-table-column>
        <el-table-column
          prop="doubt_comment"
          label="存疑理由"
          width="120">
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button
              @click.native.prevent="deleteRow(scope.$index, doubts)"
              type="text"
              size="small">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    `,
    data() {
        return {

        }
    },
    methods: {
        handleCurrentChange(val) {
            this.$emit('update:current_doubt', val);
        },
        deleteRow(index, rows) {
            axios.delete('/api/doubt_seg/'+ this.task_id+'/'+ rows[index].id +'/delete/').then(function(response) {
                  console.log(response)
                  //rows.splice(index, 1);
                  this.$delete(this.doubts, index)
                  this.$emit('update:doubts', this.doubts);
            }.bind(this))
            .catch(function (error) {
              console.log(error)
            });
        },
        loadDoubtSeg(){
            axios.get('/api/doubt_seg/'+ this.task_id+'/list/').then(function(response) {
              console.log(response)
              this.$emit('update:doubts', _.reverse(response.data.models))
            }.bind(this))
            .catch(function (error) {
              console.log(error)
            });
          }
    },
    mounted() {
        console.log('entered');
        this.loadDoubtSeg();
    }
})