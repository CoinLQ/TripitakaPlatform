Vue.component('correct-diff-seg', {
    props: ['seg', 'index'],
    template: '\
    <tr class="seg-row">\
    <td>{{ seg.text1 }}</td>\
    <td>{{ seg.text2 }}</td>\
    <td><textarea rows="1" v-model="seg.selected_text"></textarea></td>\
    </tr>\
    ',
    methods: {

    }
})