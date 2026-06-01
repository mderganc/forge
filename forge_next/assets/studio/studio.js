(function () {
  'use strict';

  var selected = new Map();
  var recentEvents = {};
  var lastFreeformFeedback = '';

  function eventKey(payload) {
    return JSON.stringify({
      type: payload.type,
      gate: payload.gate || '',
      choice: payload.choice || '',
      probe_id: payload.probe_id || '',
      text: payload.text || '',
      choices: payload.choices || null,
    });
  }

  function postEvent(payload) {
    var key = eventKey(payload);
    var now = Date.now();
    if (recentEvents[key] && now - recentEvents[key] < 900) {
      return Promise.resolve();
    }
    recentEvents[key] = now;
    var headers = { 'Content-Type': 'application/json' };
    if (window.__FORGE_STUDIO_TOKEN__) {
      headers['X-Forge-Studio-Token'] = window.__FORGE_STUDIO_TOKEN__;
    }
    return fetch('/api/event', {
      method: 'POST',
      headers: headers,
      body: JSON.stringify(payload),
    }).then(function (r) {
      return r.json().then(function (body) {
        if (!r.ok) {
          var err = body && body.error ? body.error : 'Request failed';
          return Promise.reject({ error: err, status: r.status });
        }
        return body;
      });
    }).catch(function (err) {
      if (err && err.error) return Promise.reject(err);
      return Promise.reject({ error: 'Network error' });
    });
  }

  function resolveGate() {
    var root = document.querySelector('[data-studio-gate]');
    if (root && root.getAttribute('data-studio-gate')) {
      return root.getAttribute('data-studio-gate');
    }
    var probes = document.querySelector('.studio-probes[data-gate]');
    if (probes) return probes.getAttribute('data-gate') || '';
    var notes = document.querySelector('.studio-design-notes[data-gate]');
    if (notes) return notes.getAttribute('data-gate') || '';
    var opt = document.querySelector('.option[data-gate]');
    if (opt) return opt.getAttribute('data-gate') || '';
    var box = document.querySelector('[data-multiselect][data-gate]');
    if (box) return box.getAttribute('data-gate') || '';
    return '';
  }

  function setStatus(msg, isError) {
    var el = document.getElementById('studio-feedback-status');
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? '#b91c1c' : '#15803d';
  }

  function setProbeStatus(probeEl, msg, isError) {
    var el = probeEl.querySelector('.studio-probe-status');
    if (!el) return;
    el.textContent = msg || '';
    el.style.color = isError ? '#b91c1c' : '#15803d';
  }

  window.studioToggle = function (el) {
    if (!el || !el.dataset) return;
    var gate = el.dataset.gate || resolveGate();
    var choice = el.dataset.choice || '';
    var label = (el.querySelector('.content h3') || el).textContent.trim();
    var multiselect = el.closest('[data-multiselect]');
    if (multiselect) {
      el.classList.toggle('selected');
      var key = gate || 'default';
      if (!selected.has(key)) selected.set(key, new Set());
      var set = selected.get(key);
      if (el.classList.contains('selected')) set.add(choice);
      else set.delete(choice);
      return;
    }
    if (el.classList.contains('selected')) {
      return;
    }
    document.querySelectorAll('.option.selected').forEach(function (n) {
      if (n !== el) n.classList.remove('selected');
    });
    el.classList.add('selected');
    postEvent({ type: 'click', gate: gate, choice: choice, label: label });
  };

  window.studioSubmit = function (gateId) {
    var container = gateId
      ? document.querySelector('[data-multiselect][data-gate="' + gateId + '"]')
      : document.querySelector('[data-multiselect]');
    if (!container) return;
    var gate = gateId || container.getAttribute('data-gate') || resolveGate();
    var choices = [];
    container.querySelectorAll('.option.selected').forEach(function (el) {
      if (el.dataset.choice) choices.push(el.dataset.choice);
    });
    if (!choices.length) {
      setStatus('Select at least one option first.', true);
      return;
    }
    postEvent({ type: 'submit', gate: gate, choices: choices, label: choices.join(', ') });
    setStatus('Selections sent.', false);
  };

  function probePrompt(probeEl) {
    var fromAttr = probeEl.getAttribute('data-probe-prompt');
    if (fromAttr) return fromAttr.trim();
    var p = probeEl.querySelector('.studio-probe-prompt');
    return p ? p.textContent.trim() : '';
  }

  function probeAnswer(probeEl) {
    var ta = probeEl.querySelector('.studio-probe-answer');
    return ta ? ta.value.trim() : '';
  }

  function sendProbeAnswer(probeEl, gate) {
    var probeId = probeEl.getAttribute('data-probe-id') || '';
    var prompt = probePrompt(probeEl);
    var text = probeAnswer(probeEl);
    if (!text) {
      setProbeStatus(probeEl, 'Write an answer before sending.', true);
      var ta = probeEl.querySelector('.studio-probe-answer');
      if (ta) ta.focus();
      return Promise.resolve();
    }
    var label = (probeId ? probeId + ': ' : '') + text.slice(0, 120);
    return postEvent({
      type: 'probe-response',
      gate: gate,
      probe_id: probeId,
      prompt: prompt,
      text: text,
      label: label,
    }).then(function () {
      setProbeStatus(probeEl, 'Answer sent.', false);
      probeEl.classList.add('studio-probe-answered');
    });
  }

  function initProbes() {
    var section = document.querySelector('.studio-probes');
    if (!section) return;
    var gate = section.getAttribute('data-gate') || resolveGate();

    section.querySelectorAll('.studio-probe').forEach(function (probeEl) {
      var btn = probeEl.querySelector('.studio-probe-send');
      if (!btn || btn.dataset.studioBound) return;
      btn.dataset.studioBound = '1';
      btn.addEventListener('click', function () {
        if (btn.disabled) return;
        btn.disabled = true;
        sendProbeAnswer(probeEl, gate).finally(function () {
          btn.disabled = false;
        });
      });
    });

    var submitAll = section.querySelector('.studio-probes-submit-all');
    if (submitAll && !submitAll.dataset.studioBound) {
      submitAll.dataset.studioBound = '1';
      submitAll.addEventListener('click', function () {
        if (submitAll.disabled) return;
        var responses = [];
        section.querySelectorAll('.studio-probe').forEach(function (probeEl) {
          var text = probeAnswer(probeEl);
          if (!text) return;
          responses.push({
            probe_id: probeEl.getAttribute('data-probe-id') || '',
            prompt: probePrompt(probeEl),
            text: text,
          });
        });
        if (!responses.length) {
          setStatus('Answer at least one question above.', true);
          return;
        }
        submitAll.disabled = true;
        postEvent({
          type: 'probes-submit',
          gate: gate,
          responses: responses,
          label: responses.map(function (r) {
            return (r.probe_id || 'q') + ': ' + r.text.slice(0, 40);
          }).join(' | '),
        }).then(function () {
          section.querySelectorAll('.studio-probe').forEach(function (probeEl) {
            setProbeStatus(probeEl, 'Included in batch.', false);
            probeEl.classList.add('studio-probe-answered');
          });
          setStatus('All answers sent.', false);
        }).finally(function () {
          submitAll.disabled = false;
        });
      });
    }
  }

  function initFeedback() {
    var panel = document.querySelector('[data-studio-feedback]');
    if (!panel) return;
    var gate = resolveGate();
    if (gate) panel.setAttribute('data-gate', gate);

    var btnSend = panel.querySelector('.studio-submit-feedback');
    var btnApprove = panel.querySelector('.studio-approve-screen');
    var btnUnlock = panel.querySelector('.studio-unlock-screen');
    var btnDone = panel.querySelector('.studio-mark-done');
    var textarea = document.getElementById('studio-feedback-text');

    function refreshLockButtons() {
      var gateId = gate || resolveGate();
      if (!gateId) return;
      fetch('/api/locks')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          var locked = (d.gates || []).indexOf(gateId) >= 0;
          if (btnApprove) btnApprove.hidden = locked;
          if (btnUnlock) btnUnlock.hidden = !locked;
          if (locked) panel.classList.add('studio-screen-approved');
          else panel.classList.remove('studio-screen-approved');
        })
        .catch(function () {});
    }

    if (btnSend && textarea && !btnSend.dataset.studioBound) {
      btnSend.dataset.studioBound = '1';
      btnSend.addEventListener('click', function () {
        if (btnSend.disabled) return;
        var text = textarea.value.trim();
        if (!text) {
          setStatus('Write feedback before sending.', true);
          textarea.focus();
          return;
        }
        btnSend.disabled = true;
        postEvent({
          type: 'feedback',
          gate: gate || resolveGate(),
          text: text,
          label: text.slice(0, 120),
        }).then(function () {
          lastFreeformFeedback = text;
          setStatus('Feedback sent. You can add more or click Done reviewing.', false);
          textarea.value = '';
        }).finally(function () {
          btnSend.disabled = false;
        });
      });
    }

    if (btnApprove && !btnApprove.dataset.studioBound) {
      btnApprove.dataset.studioBound = '1';
      btnApprove.addEventListener('click', function () {
        if (btnApprove.disabled) return;
        btnApprove.disabled = true;
        postEvent({
          type: 'approve',
          gate: gate || resolveGate(),
          label: 'User approved screen (lock as reference)',
        }).then(function () {
          setStatus('Screen approved and locked for planning/implement.', false);
          refreshLockButtons();
        }).catch(function (err) {
          setStatus((err && err.error) || 'Approve failed.', true);
        }).finally(function () {
          btnApprove.disabled = false;
        });
      });
    }

    if (btnUnlock && !btnUnlock.dataset.studioBound) {
      btnUnlock.dataset.studioBound = '1';
      btnUnlock.addEventListener('click', function () {
        if (btnUnlock.disabled) return;
        btnUnlock.disabled = true;
        postEvent({
          type: 'unlock',
          gate: gate || resolveGate(),
          label: 'User unlocked screen for editing',
        }).then(function () {
          setStatus('Screen unlocked — you can iterate and approve again.', false);
          refreshLockButtons();
        }).catch(function (err) {
          setStatus((err && err.error) || 'Unlock failed.', true);
        }).finally(function () {
          btnUnlock.disabled = false;
        });
      });
    }

    refreshLockButtons();

    if (btnDone && !btnDone.dataset.studioBound) {
      btnDone.dataset.studioBound = '1';
      btnDone.addEventListener('click', function () {
        if (btnDone.disabled) return;
        btnDone.disabled = true;
        var extra = textarea && textarea.value.trim();
        var chain = Promise.resolve();
        if (extra && extra !== lastFreeformFeedback) {
          chain = postEvent({
            type: 'feedback',
            gate: gate || resolveGate(),
            text: extra,
            label: extra.slice(0, 120),
          });
        }
        chain.then(function () {
          return postEvent({
            type: 'done',
            gate: gate || resolveGate(),
            label: 'User finished reviewing screen',
          });
        }).then(function () {
          setStatus('Marked done — continue in chat when ready.', false);
        }).finally(function () {
          btnDone.disabled = false;
        });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-studio-submit]').forEach(function (btn) {
      if (btn.dataset.studioBound) return;
      btn.dataset.studioBound = '1';
      btn.addEventListener('click', function () {
        studioSubmit(btn.getAttribute('data-studio-submit') || '');
      });
    });
    initProbes();
    initFeedback();

    var lastVersion = -1;
    setInterval(function () {
      fetch('/api/version')
        .then(function (r) { return r.json(); })
        .then(function (d) {
          if (typeof d.version === 'number' && d.version !== lastVersion) {
            if (lastVersion >= 0) location.reload();
            lastVersion = d.version;
          }
        })
        .catch(function () {});
    }, 1500);
  });
})();
