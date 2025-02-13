function searchMedicine() {
    let medicineName = document.getElementById("medicineInput").value;
    if (!medicineName) {
        alert("Please enter a medicine name");
        return;
    }

    document.getElementById("result").innerHTML = "Searching...";

    fetch(`http://127.0.0.1:5000/search?medicine=${encodeURIComponent(medicineName)}`)
        .then(response => response.json())
        .then(data => {
            let resultHTML = `<h3>${data.medicine}</h3><p><b>Usage:</b> ${data.usage}</p>`;
            if (data.links.length > 0) {
                resultHTML += "<h4>More Information:</h4><ul>";
                data.links.forEach(link => {
                    resultHTML += `<li><a href="${link}" target="_blank">${link}</a></li>`;
                });
                resultHTML += "</ul>";
            } else {
                resultHTML += "<p>No additional sources found.</p>";
            }
            document.getElementById("result").innerHTML = resultHTML;
        })
        .catch(error => {
            console.error("Error:", error);
            document.getElementById("result").innerHTML = "Failed to fetch data";
        });
}
