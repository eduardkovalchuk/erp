// Call the dataTables jQuery plugin
$('#formula_table').dataTable({
  "searching": false,
  language: {
    "lengthMenu": "Показати _MENU_ на сторінку",
    "zeroRecords": "Нічого не знайдено",
    "info": "Показано _PAGE_ з _PAGES_",
    "infoEmpty": "Немає доступних записів",
    "paginate":{
      "previous":"Попередня",
      "next":"Наступна",
    },
  },
});
