(function () {
    'use strict';

    const knownFiles = new Set();
    const confirmedDraft = []; // Array to store all confirmed picks and bans
    const ANALYZER_URL = 'http://localhost:5000/update_draft';

    async function sendToAnalyzer(data) {
        try {
            const response = await fetch(ANALYZER_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                mode: 'cors',
                body: JSON.stringify(data)
            });
            if (response.ok) {
                // If it's a regular pick, log the filename
                const name = data.current ? data.current.heroFile : "SYNC";
                console.log(`%c[SENT]: ${name} to analyzer.`, "color: #2ecc71; font-weight: bold;");
            }
        } catch (err) {
            console.warn("%c[OFFLINE]: Analyzer server not found at " + ANALYZER_URL, "color: #e74c3c;");
        }
    }

    function checkDraft() {
        // 1. PRE-SELECTION FILTER
        const activeConfirmBtn = document.querySelector('.confirm-btn:not([disabled])');
        if (activeConfirmBtn) return;

        // 2. SCAN FOR HERO IMAGES IN TEAM PANELS
        const draftImages = document.querySelectorAll('.team-panel img[src*="heroes"]');
        const screenWidth = window.innerWidth;

        draftImages.forEach(img => {
            const src = img.src;
            const decodedSrc = decodeURIComponent(src);
            const fileName = decodedSrc.split('/').pop();

            if (fileName.toLowerCase() === 'heroes.png' || knownFiles.has(fileName)) return;

            // 3. STABILITY CHECK (Opacity)
            if (window.getComputedStyle(img).opacity < 0.9) return;

            // 4. COORDINATE-BASED TEAM DETECTION
            const rect = img.getBoundingClientRect();
            const centerX = rect.left + (rect.width / 2);
            let teamName = (centerX < screenWidth / 2) ? 'AMBER' : 'SAPPHIRE';

            // 5. ACTION TYPE DETECTION
            const isBan = img.closest('.team-bans') !== null;
            const type = isBan ? 'BAN' : 'PICK';

            // 6. REGISTER NEW HERO
            knownFiles.add(fileName);

            const entry = {
                team: teamName,
                type: type,
                heroFile: fileName
            };

            // Add to local history array
            confirmedDraft.push(entry);

            // LOG to browser console
            const teamColor = teamName === 'SAPPHIRE' ? '#3498db' : '#f39c12';
            console.log(
                `%c[${teamName}] [${type}]: ${fileName}`,
                `background: ${teamColor}; color: white; padding: 3px 6px; font-weight: bold; border-radius: 4px;`
            );

            // 7. SEND: Current pick + Full history for verification
            sendToAnalyzer({
                event: 'DRAFT_UPDATE',
                current: entry,
                fullDraft: confirmedDraft,
                count: confirmedDraft.length,
                timestamp: new Date().toISOString()
            });
        });

        // 8. DRAFT COMPLETION
        if (document.querySelector('.draft-complete-controls') && !window.draftFinished) {
            window.draftFinished = true;
            sendToAnalyzer({
                event: 'DRAFT_COMPLETE',
                fullDraft: confirmedDraft,
                count: confirmedDraft.length,
                timestamp: new Date().toISOString()
            });
            console.log("%c--- DRAFT FINISHED ---", "background: #000; color: #fff; padding: 5px; font-weight: bold;");
        }
    }

    const observer = new MutationObserver(checkDraft);
    observer.observe(document.body, { childList: true, subtree: true });
    setInterval(checkDraft, 1000);

    console.log("%c[Watcher] Analyzer integration active. Monitoring with Sync support...", "color: #3498db; font-weight: bold;");
})();