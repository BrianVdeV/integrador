function checkAndHighlightDate(row, dateStr, columnIdx) {
  var date = moment(dateStr, "YYYY-MM-DD", true);
  if (date.isValid()) {
    var daysDifference = date.diff(moment(), "days");
    var colorClass = getColorClass(daysDifference);
    if (colorClass) {
      $(row)
        .find("td:eq(" + columnIdx + ")")
        .addClass("text-" + colorClass);
    }
  }
}

function getColorClass(daysDifference) {
  if (daysDifference >= 0 && daysDifference <= 3) {
    return "danger";
  } else if (daysDifference > 3 && daysDifference <= 7) {
    return "warning";
  }
  return "";
}

//Select2
$("#ot").select2({
  dropdownParent: $("#mdlAddExp"),
});
