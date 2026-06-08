(function () {
  if (typeof graphData === "undefined" || !document.getElementById("courbe-temp")) return;

  const ctx = document.getElementById("courbe-temp").getContext("2d");

  const pointColors = graphData.point_styles;
  const pointRadii = graphData.point_radius;
  const borderDash = graphData.border_dash;

  const datasets = [
    {
      label: "Température",
      data: graphData.data_corrigee,
      borderColor: "#5a9b91",
      backgroundColor: pointColors,
      pointBackgroundColor: pointColors,
      pointBorderColor: pointColors,
      pointRadius: pointRadii,
      pointBorderDash: borderDash,
      tension: 0.2,
      spanGaps: false,
    },
  ];

  if (graphData.ligne_reference && graphData.ligne_reference.length) {
    datasets.push({
      label: "Ligne de référence",
      data: graphData.ligne_reference,
      borderColor: "#e88f70",
      borderDash: [6, 4],
      pointRadius: 0,
      borderWidth: 2,
      fill: false,
    });
  }

  const annotations = {};
  if (graphData.pic_index !== null && graphData.pic_index !== undefined) {
    datasets[0].pointBackgroundColor = graphData.point_styles.map((c, i) =>
      i === graphData.pic_index ? "#7c3aed" : c
    );
    datasets[0].pointRadius = graphData.point_radius.map((r, i) =>
      i === graphData.pic_index ? 11 : r
    );
  }

  new Chart(ctx, {
    type: "line",
    data: { labels: graphData.labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            afterLabel: function (ctx) {
              if (ctx.datasetIndex === 0 && graphData.data_brute[ctx.dataIndex] != null) {
                const brute = graphData.data_brute[ctx.dataIndex];
                const corr = graphData.data_corrigee[ctx.dataIndex];
                if (brute !== corr) return "Brute : " + brute + " °C";
              }
              return "";
            },
          },
        },
      },
      scales: {
        y: {
          title: { display: true, text: "°C" },
          suggestedMin: 35.5,
          suggestedMax: 37.5,
        },
      },
    },
  });
})();
