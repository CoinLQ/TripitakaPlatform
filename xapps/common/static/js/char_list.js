var char_list = new Vue({
    el: '#charListArea',
    data: {
        selection: 0,
        detect_selection: 0,
        detect_type: 0,
        detect_page: 1,
        detect_pagination: {},
        item_id: '',
        item_url: '',
        item_direct: '',
        items: charListContainer.data,
        detect_items: [],
        degree: 0,
        final_degree: 0,
        detecting: false,
        menu_style: {
            top: 0,
            left: 0,
            display: 'none'
        },
        detect_menu_style:{
            top: 0,
            left: 0,
            display: 'none'
        },
        predict_results: []
    },

    csrf_token: '{{ csrf_token }}',
    methods: {
        gen_cls: function(item) {
            var class_name;
            if (item.is_correct == 1) {
                cls_name = 'correct-char flip-inx'
            } else if (item.is_correct == -1) {
                cls_name = 'error-char flip-inx'
            } else {
                cls_name = 'twinkling'
            }
            // if (this.items.indexOf(item) == this.selection)
            //     cls_name = cls_name.replace(/flip-inx/, '')
            return cls_name;
        },
        gen_detect_cls:  function(item) {
            var class_name;
            if (item.is_correct == 1) {
               cls_name = !item.checked ? 'correct-char flip-inx' : 'error-char flip-inx'
            } else if (item.is_correct == -1) {
                cls_name = !item.checked ? 'error-char flip-inx' : 'correct-char flip-inx'
            } else {
                cls_name = !item.checked ? 'twinkling' : 'correct-char flip-inx'
            }
            return cls_name;
        },
    }
});